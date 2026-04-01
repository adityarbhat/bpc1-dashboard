"""
W&C (Wins & Challenges) Excel Parser
Parses the W&C upload template with 3 sheets: Wins, Challenges, Action Items
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Any


def _sanitize_text(text: str) -> str:
    """
    Strip markdown and LaTeX formatting from Excel cell text so it renders
    as clean plain text on the dashboard.

    Handles:
    - **bold** markers
    - `inline code` backticks (renders as green monospace)
    - $LaTeX math$ dollar signs (renders as large serif font)
    - Excess whitespace
    """
    # Strip LaTeX math: $...$ → inner content
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    # Strip bold: **text** → text
    text = re.sub(r'\*\*([^*]*)\*\*', r'\1', text)
    # Strip remaining lone ** markers
    text = text.replace('**', '')
    # Strip inline code backticks: `text` → text
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_wc_excel(uploaded_file) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parse W&C Excel file with 3 data sheets.

    Args:
        uploaded_file: Streamlit uploaded file object

    Returns:
        Tuple of (results_dict, warnings_list)

        results_dict = {
            'wins': [{'text': str, 'display_order': int}, ...],
            'challenges': [{'text': str, 'display_order': int}, ...],
            'action_items': [{'text': str, 'display_order': int}, ...],
            'wins_count': int,
            'challenges_count': int,
            'action_items_count': int
        }
    """
    results = {
        'wins': [],
        'challenges': [],
        'action_items': [],
        'wins_count': 0,
        'challenges_count': 0,
        'action_items_count': 0
    }
    warnings = []

    # Parse each sheet
    wins, wins_warnings = _parse_wc_sheet(uploaded_file, "Wins", "win")
    results['wins'] = wins
    results['wins_count'] = len(wins)
    warnings.extend(wins_warnings)

    challenges, challenges_warnings = _parse_wc_sheet(uploaded_file, "Challenges", "challenge")
    results['challenges'] = challenges
    results['challenges_count'] = len(challenges)
    warnings.extend(challenges_warnings)

    action_items, action_items_warnings = _parse_wc_sheet(uploaded_file, "Action Items", "action_item")
    results['action_items'] = action_items
    results['action_items_count'] = len(action_items)
    warnings.extend(action_items_warnings)

    return results, warnings


def _parse_wc_sheet(uploaded_file, sheet_name: str, item_type: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse a single W&C sheet.

    Args:
        uploaded_file: Streamlit uploaded file object
        sheet_name: "Wins", "Challenges", or "Action Items"
        item_type: "win", "challenge", or "action_item" (for error messages)

    Returns:
        Tuple of (items_list, warnings_list)
        items_list = [{'text': str, 'display_order': int}, ...]
    """
    items = []
    warnings = []

    try:
        # Read the sheet
        # Skip first 3 rows: title, headers, instruction
        df = pd.read_excel(
            uploaded_file,
            sheet_name=sheet_name,
            header=None,  # No header row - we'll parse manually
            skiprows=3    # Skip title, header, and instruction rows
        )

        # Reset file pointer for next sheet
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)

        if df.empty:
            return items, warnings

        # Process each row
        auto_order = 1
        for idx, row in df.iterrows():
            # Column A (index 0): Text content
            # Column B (index 1): Display order
            text = row.iloc[0] if len(row) > 0 else None
            display_order = row.iloc[1] if len(row) > 1 else None

            # Skip empty text rows
            if pd.isna(text) or str(text).strip() == '':
                continue

            text = _sanitize_text(str(text))

            # Validate text length
            if len(text) > 5000:
                warnings.append(f"{sheet_name} row {idx + 4}: Text exceeds 5000 characters (truncated)")
                text = text[:5000]

            # Handle display order
            if pd.isna(display_order) or display_order == '':
                order = auto_order
            else:
                try:
                    order = int(display_order)
                except (ValueError, TypeError):
                    warnings.append(f"{sheet_name} row {idx + 4}: Invalid display order '{display_order}', using {auto_order}")
                    order = auto_order

            items.append({
                'text': text,
                'display_order': order
            })
            auto_order += 1

    except ValueError as e:
        # Sheet not found
        if "not found" in str(e).lower():
            warnings.append(f"Sheet '{sheet_name}' not found in uploaded file")
        else:
            warnings.append(f"Error reading '{sheet_name}' sheet: {str(e)}")
    except Exception as e:
        warnings.append(f"Error parsing '{sheet_name}' sheet: {str(e)}")

    return items, warnings


def validate_wc_data(results: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate parsed W&C data.

    Args:
        results: The results dict from parse_wc_excel

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check if at least one item exists
    total_items = results['wins_count'] + results['challenges_count'] + results['action_items_count']
    if total_items == 0:
        errors.append("No items found in the uploaded file. Please add at least one win, challenge, or action item.")
        return False, errors

    return True, errors
