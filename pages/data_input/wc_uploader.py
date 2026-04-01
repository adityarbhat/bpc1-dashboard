"""
W&C (Wins & Challenges) Uploader
Handles uploading W&C data to Airtable with overwrite support
"""

import os
import requests
import streamlit as st
from typing import Dict, List, Tuple, Any
from datetime import datetime
from pages.data_input.wins_challenges_manager import WinsChallengesActionItemsManager, _escape_airtable_value


def get_airtable_credentials():
    """Get Airtable credentials from secrets or environment"""
    try:
        airtable_base_id = st.secrets.get("AIRTABLE_BASE_ID")
        airtable_pat = st.secrets.get("AIRTABLE_PAT")
    except Exception:
        airtable_base_id = None
        airtable_pat = None

    airtable_base_id = airtable_base_id or os.getenv("AIRTABLE_BASE_ID")
    airtable_pat = airtable_pat or os.getenv("AIRTABLE_PAT")

    return airtable_base_id, airtable_pat


def upload_wc_to_airtable(
    company_name: str,
    period_name: str,
    wins: List[Dict],
    challenges: List[Dict],
    action_items: List[Dict]
) -> Tuple[bool, str, Dict[str, int]]:
    """
    Upload W&C data to Airtable as DRAFT.
    Overwrites existing drafts for the same company/period.

    Args:
        company_name: Company name
        period_name: Period name (e.g., "2024 Annual")
        wins: List of {'text': str, 'display_order': int}
        challenges: List of {'text': str, 'display_order': int}
        action_items: List of {'text': str, 'display_order': int}

    Returns:
        Tuple of (success, message, counts_dict)
        counts_dict = {'wins': n, 'challenges': n, 'action_items': n}
    """
    counts = {'wins': 0, 'challenges': 0, 'action_items': 0}

    try:
        # Get credentials
        airtable_base_id, airtable_pat = get_airtable_credentials()
        if not airtable_base_id or not airtable_pat:
            return False, "Airtable credentials not configured", counts

        # Initialize manager
        manager = WinsChallengesActionItemsManager(airtable_base_id, airtable_pat)

        # Get period ID
        period_id = manager.get_period_id(company_name, period_name)
        if not period_id:
            return False, f"Period '{period_name}' not found for company '{company_name}'", counts

        # Step 1: Delete all existing records for this period (overwrite behavior)
        deleted = _delete_existing_records(manager, period_id)

        # Step 2: Create new records as drafts
        errors = []

        # Upload wins
        for item in wins:
            success, record_id, message = manager.create_win(
                period_id=period_id,
                win_text=item['text'],
                display_order=item['display_order'],
                status='draft',
                name=company_name
            )
            if success:
                counts['wins'] += 1
            else:
                errors.append(f"Win: {message}")

        # Upload challenges
        for item in challenges:
            success, record_id, message = manager.create_challenge(
                period_id=period_id,
                challenge_text=item['text'],
                display_order=item['display_order'],
                status='draft',
                name=company_name
            )
            if success:
                counts['challenges'] += 1
            else:
                errors.append(f"Challenge: {message}")

        # Upload action items
        for item in action_items:
            success, record_id, message = manager.create_action_item(
                period_id=period_id,
                action_item_text=item['text'],
                display_order=item['display_order'],
                status='draft',
                name=company_name
            )
            if success:
                counts['action_items'] += 1
            else:
                errors.append(f"Action Item: {message}")

        # Build result message
        total_created = counts['wins'] + counts['challenges'] + counts['action_items']
        total_deleted = deleted['wins'] + deleted['challenges'] + deleted['action_items']

        if errors:
            error_msg = "; ".join(errors[:3])  # Show first 3 errors
            if len(errors) > 3:
                error_msg += f" (+{len(errors) - 3} more errors)"
            return False, f"Partial upload. Created {total_created} items. Errors: {error_msg}", counts

        message = f"Successfully uploaded {total_created} items as DRAFT"
        if total_deleted > 0:
            message += f" (replaced {total_deleted} existing drafts)"

        return True, message, counts

    except Exception as e:
        return False, f"Upload failed: {str(e)}", counts


def _delete_existing_records(manager: WinsChallengesActionItemsManager, period_id: str) -> Dict[str, int]:
    """
    Hard delete all active records for a period (both draft and published) to allow clean overwrite.
    Fetches all active records and filters by period_id in Python — avoids unreliable ARRAYJOIN
    on linked record fields.

    Args:
        manager: WinsChallengesActionItemsManager instance
        period_id: Airtable record ID for the period

    Returns:
        Dict with counts: {'wins': n, 'challenges': n, 'action_items': n}
    """
    deleted = {'wins': 0, 'challenges': 0, 'action_items': 0}

    tables = [
        ('wins', 'wins'),
        ('challenges', 'challenges'),
        ('action_items', 'action_items')
    ]

    for table_name, count_key in tables:
        try:
            # Fetch all active records, then filter by period_id in Python
            # (ARRAYJOIN on linked fields is unreliable — same pattern as airtable_connection.py)
            url = f"{manager.base_url}/{table_name}"
            params = {'filterByFormula': '{is_active}=TRUE()'}

            response = requests.get(url, headers=manager.headers, params=params)
            if response.status_code != 200:
                continue

            all_records = response.json().get('records', [])
            # Filter to only records linked to this period
            records = [
                r for r in all_records
                if period_id in r.get('fields', {}).get('period', [])
            ]
            if not records:
                continue

            # Delete records in batches of 10 (Airtable limit)
            record_ids = [r['id'] for r in records]
            for i in range(0, len(record_ids), 10):
                batch_ids = record_ids[i:i+10]
                delete_params = {'records[]': batch_ids}
                delete_response = requests.delete(url, headers=manager.headers, params=delete_params)

                if delete_response.status_code == 200:
                    deleted[count_key] += len(batch_ids)

        except Exception:
            # Log but continue - don't fail the whole upload
            pass

    return deleted


def get_draft_counts_for_period(company_name: str, period_name: str) -> Dict[str, int]:
    """
    Get count of existing draft records for a company/period.
    Used to show warning before overwrite.

    Returns:
        {'wins': n, 'challenges': n, 'action_items': n}
    """
    counts = {'wins': 0, 'challenges': 0, 'action_items': 0}

    try:
        airtable_base_id, airtable_pat = get_airtable_credentials()
        if not airtable_base_id or not airtable_pat:
            return counts

        manager = WinsChallengesActionItemsManager(airtable_base_id, airtable_pat)
        period_id = manager.get_period_id(company_name, period_name)

        if not period_id:
            return counts

        # Get draft counts for each table
        for table_name in ['wins', 'challenges', 'action_items']:
            items = manager.get_items_by_status(table_name, period_id, status='draft')
            counts[table_name] = len(items) if items else 0

    except Exception:
        pass

    return counts
