"""
Wins, Challenges & Action Items Manager
Handles create, update, and delete operations for wins, challenges, and action items in Airtable
"""

import requests
import streamlit as st
from datetime import datetime


class WinsChallengesActionItemsManager:
    """Manager class for wins, challenges, and action items CRUD operations"""

    def __init__(self, base_id, personal_access_token):
        self.base_id = base_id
        self.pat = personal_access_token
        self.headers = {
            'Authorization': f'Bearer {personal_access_token}',
            'Content-Type': 'application/json'
        }
        self.base_url = f"https://api.airtable.com/v0/{base_id}"

    # ==================== HELPER METHODS ====================

    def get_period_id(self, company_name, period_name):
        """
        Get the period record ID for a company+period combination

        Note: company field is a linked record, so we use FIND to search within the array
        """
        try:
            url = f"{self.base_url}/financial_periods"
            # Use FIND to search for company name within linked field
            filter_formula = f"AND(FIND('{company_name}', ARRAYJOIN({{company}})), {{period_name}}='{period_name}')"
            params = {'filterByFormula': filter_formula}

            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                if records:
                    return records[0]['id']
            # Add debug info
            st.warning(f"No period found for company '{company_name}' and period '{period_name}'")
            st.warning(f"Response status: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Error getting period ID: {str(e)}")
            return None

    def validate_text(self, text):
        """Validate that text is not empty"""
        if not text or not text.strip():
            return False, "Text cannot be empty"
        if len(text) > 5000:
            return False, "Text is too long (max 5000 characters)"
        return True, ""

    def validate_display_order(self, order):
        """Validate display order"""
        try:
            order_num = int(order)
            if order_num < 1:
                return False, "Display order must be at least 1"
            return True, ""
        except (ValueError, TypeError):
            return False, "Display order must be a number"

    # ==================== WINS METHODS ====================

    def create_win(self, period_id, win_text, display_order=1, status='draft', name=None):
        """Create a new win record

        Args:
            period_id: Airtable record ID for the period
            win_text: The win description
            display_order: Sort order (default: 1)
            status: 'draft' or 'published' (default: 'draft')
            name: Company name for the name field (optional)
        """
        # Validate inputs
        is_valid, error_msg = self.validate_text(win_text)
        if not is_valid:
            return False, None, error_msg

        is_valid, error_msg = self.validate_display_order(display_order)
        if not is_valid:
            return False, None, error_msg

        # Create record
        record = {
            'period': [period_id],
            'win_text': win_text.strip(),
            'display_order': int(display_order),
            'is_active': True,
            'status': status,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        if name:
            record['Name'] = name

        url = f"{self.base_url}/wins"
        payload = {"records": [{"fields": record}]}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                record_id = response.json()['records'][0]['id']
                return True, record_id, "Win created successfully"
            else:
                return False, None, f"API Error: {response.text}"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def update_win(self, record_id, updates):
        """Update an existing win record"""
        # Validate text if it's being updated
        if 'win_text' in updates:
            is_valid, error_msg = self.validate_text(updates['win_text'])
            if not is_valid:
                return False, error_msg
            updates['win_text'] = updates['win_text'].strip()

        # Validate display order if it's being updated
        if 'display_order' in updates:
            is_valid, error_msg = self.validate_display_order(updates['display_order'])
            if not is_valid:
                return False, error_msg
            updates['display_order'] = int(updates['display_order'])

        url = f"{self.base_url}/wins/{record_id}"
        payload = {"fields": updates}

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                return True, "Win updated successfully"
            else:
                return False, f"API Error: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_win(self, record_id):
        """Soft delete a win by setting is_active to False"""
        return self.update_win(record_id, {'is_active': False})

    def batch_update_wins(self, updates_list):
        """Batch update multiple wins"""
        results = []
        for update in updates_list:
            record_id = update.get('id')
            fields = update.get('fields', {})
            success, message = self.update_win(record_id, fields)
            results.append({'id': record_id, 'success': success, 'message': message})
        return results

    # ==================== CHALLENGES METHODS ====================

    def create_challenge(self, period_id, challenge_text, display_order=1, status='draft', name=None):
        """Create a new challenge record

        Args:
            period_id: Airtable record ID for the period
            challenge_text: The challenge description
            display_order: Sort order (default: 1)
            status: 'draft' or 'published' (default: 'draft')
            name: Company name for the name field (optional)
        """
        # Validate inputs
        is_valid, error_msg = self.validate_text(challenge_text)
        if not is_valid:
            return False, None, error_msg

        is_valid, error_msg = self.validate_display_order(display_order)
        if not is_valid:
            return False, None, error_msg

        # Create record
        record = {
            'period': [period_id],
            'challenge_text': challenge_text.strip(),
            'display_order': int(display_order),
            'is_active': True,
            'status': status,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        if name:
            record['Name'] = name

        url = f"{self.base_url}/challenges"
        payload = {"records": [{"fields": record}]}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                record_id = response.json()['records'][0]['id']
                return True, record_id, "Challenge created successfully"
            else:
                return False, None, f"API Error: {response.text}"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def update_challenge(self, record_id, updates):
        """Update an existing challenge record"""
        # Validate text if it's being updated
        if 'challenge_text' in updates:
            is_valid, error_msg = self.validate_text(updates['challenge_text'])
            if not is_valid:
                return False, error_msg
            updates['challenge_text'] = updates['challenge_text'].strip()

        # Validate display order if it's being updated
        if 'display_order' in updates:
            is_valid, error_msg = self.validate_display_order(updates['display_order'])
            if not is_valid:
                return False, error_msg
            updates['display_order'] = int(updates['display_order'])

        url = f"{self.base_url}/challenges/{record_id}"
        payload = {"fields": updates}

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                return True, "Challenge updated successfully"
            else:
                return False, f"API Error: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_challenge(self, record_id):
        """Soft delete a challenge by setting is_active to False"""
        return self.update_challenge(record_id, {'is_active': False})

    def batch_update_challenges(self, updates_list):
        """Batch update multiple challenges"""
        results = []
        for update in updates_list:
            record_id = update.get('id')
            fields = update.get('fields', {})
            success, message = self.update_challenge(record_id, fields)
            results.append({'id': record_id, 'success': success, 'message': message})
        return results

    # ==================== ACTION ITEMS METHODS ====================

    def create_action_item(self, period_id, action_item_text, display_order=1, status='draft', name=None):
        """Create a new action item record

        Args:
            period_id: Airtable record ID for the period
            action_item_text: The action item description
            display_order: Sort order (default: 1)
            status: 'draft' or 'published' (default: 'draft')
            name: Company name for the name field (optional)
        """
        # Validate inputs
        is_valid, error_msg = self.validate_text(action_item_text)
        if not is_valid:
            return False, None, error_msg

        is_valid, error_msg = self.validate_display_order(display_order)
        if not is_valid:
            return False, None, error_msg

        # Create record
        record = {
            'period': [period_id],
            'action_item_text': action_item_text.strip(),
            'display_order': int(display_order),
            'is_active': True,
            'status': status,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        if name:
            record['Name'] = name

        url = f"{self.base_url}/action_items"
        payload = {"records": [{"fields": record}]}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                record_id = response.json()['records'][0]['id']
                return True, record_id, "Action item created successfully"
            else:
                return False, None, f"API Error: {response.text}"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def update_action_item(self, record_id, updates):
        """Update an existing action item record"""
        # Validate text if it's being updated
        if 'action_item_text' in updates:
            is_valid, error_msg = self.validate_text(updates['action_item_text'])
            if not is_valid:
                return False, error_msg
            updates['action_item_text'] = updates['action_item_text'].strip()

        # Validate display order if it's being updated
        if 'display_order' in updates:
            is_valid, error_msg = self.validate_display_order(updates['display_order'])
            if not is_valid:
                return False, error_msg
            updates['display_order'] = int(updates['display_order'])

        url = f"{self.base_url}/action_items/{record_id}"
        payload = {"fields": updates}

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                return True, "Action item updated successfully"
            else:
                return False, f"API Error: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_action_item(self, record_id):
        """Soft delete an action item by setting is_active to False"""
        return self.update_action_item(record_id, {'is_active': False})

    def batch_update_action_items(self, updates_list):
        """Batch update multiple action items"""
        results = []
        for update in updates_list:
            record_id = update.get('id')
            fields = update.get('fields', {})
            success, message = self.update_action_item(record_id, fields)
            results.append({'id': record_id, 'success': success, 'message': message})
        return results

    # ==================== PUBLISH METHODS ====================

    def publish_wins(self, period_id):
        """Publish all draft wins for a period (set status='published')

        Args:
            period_id: Airtable record ID for the period

        Returns:
            tuple: (success: bool, count: int, message: str)
        """
        return self._publish_items('wins', period_id)

    def publish_challenges(self, period_id):
        """Publish all draft challenges for a period (set status='published')

        Args:
            period_id: Airtable record ID for the period

        Returns:
            tuple: (success: bool, count: int, message: str)
        """
        return self._publish_items('challenges', period_id)

    def publish_action_items(self, period_id):
        """Publish all draft action items for a period (set status='published')

        Args:
            period_id: Airtable record ID for the period

        Returns:
            tuple: (success: bool, count: int, message: str)
        """
        return self._publish_items('action_items', period_id)

    def _publish_items(self, table_name, period_id):
        """Internal method to publish all draft items for a table/period

        Args:
            table_name: 'wins', 'challenges', or 'action_items'
            period_id: Airtable record ID for the period

        Returns:
            tuple: (success: bool, count: int, message: str)
        """
        try:
            # Fetch all draft records for this period
            url = f"{self.base_url}/{table_name}"
            filter_formula = f"AND(FIND('{period_id}', ARRAYJOIN({{period}})), {{status}}='draft', {{is_active}}=TRUE())"
            params = {'filterByFormula': filter_formula}

            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                return False, 0, f"Failed to fetch records: {response.text}"

            records = response.json().get('records', [])
            if not records:
                return True, 0, "No draft items to publish"

            # Batch update to published (max 10 per request for Airtable)
            published_count = 0
            for i in range(0, len(records), 10):
                batch = records[i:i+10]
                payload = {
                    'records': [
                        {'id': r['id'], 'fields': {'status': 'published'}}
                        for r in batch
                    ]
                }

                update_response = requests.patch(url, headers=self.headers, json=payload)
                if update_response.status_code == 200:
                    published_count += len(batch)
                else:
                    return False, published_count, f"Batch update failed: {update_response.text}"

            return True, published_count, f"Published {published_count} {table_name.replace('_', ' ')}"

        except Exception as e:
            return False, 0, f"Error publishing: {str(e)}"

    def get_items_by_status(self, table_name, period_id, status=None):
        """Get items for a period, optionally filtered by status

        Args:
            table_name: 'wins', 'challenges', or 'action_items'
            period_id: Airtable record ID for the period
            status: 'draft', 'published', or None for all

        Returns:
            list: List of records
        """
        try:
            url = f"{self.base_url}/{table_name}"

            if status:
                filter_formula = f"AND(FIND('{period_id}', ARRAYJOIN({{period}})), {{status}}='{status}', {{is_active}}=TRUE())"
            else:
                filter_formula = f"AND(FIND('{period_id}', ARRAYJOIN({{period}})), {{is_active}}=TRUE())"

            params = {
                'filterByFormula': filter_formula,
                'sort[0][field]': 'display_order',
                'sort[0][direction]': 'asc'
            }

            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get('records', [])
            return []

        except Exception as e:
            st.error(f"Error fetching items: {str(e)}")
            return []
