# Feature Deep Dive: Publication Control System

## Overview

This deep dive covers the publication control system that manages the lifecycle of financial data from submission to publication. You'll learn about the draft/publish workflow, permission-based access, and how data visibility is controlled.

**What You'll Learn:**
- Draft/publish workflow architecture
- Status-based data filtering
- Admin publication UI
- Batch update patterns
- Access control for published vs draft data

**Difficulty:** Intermediate
**Time:** 30-45 minutes

---

## The Publication Challenge

### Requirements

Build a publication system that:
1. Allows users to submit data without immediate visibility
2. Gives admins review and approval capability
3. Filters dashboard queries to show only published data
4. Supports bulk publication by period
5. Tracks submission metadata (who, when)

### Data Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Lifecycle                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│   │    DRAFT     │ ───▶ │  SUBMITTED   │ ───▶ │  PUBLISHED   │ │
│   │              │      │              │      │              │ │
│   │  User saves  │      │  User clicks │      │  Admin       │ │
│   │  W&C data    │      │  "Submit"    │      │  approves    │ │
│   └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      │                      │         │
│         ▼                      ▼                      ▼         │
│   Hidden from all       Hidden from         Visible to all     │
│   dashboard users       company users       dashboard users    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Status Fields

### Financial Data (Balance Sheet / Income Statement)

```python
# Field: publication_status
# Values: None (blank), 'submitted', 'published'

# Blank/None: Legacy data or admin-entered data (visible)
# 'submitted': User uploaded, awaiting admin review (hidden)
# 'published': Admin approved, visible to all
```

### Wins & Challenges

```python
# Field: status
# Values: 'draft', 'published'

# 'draft': User uploaded, awaiting admin review (hidden)
# 'published': Admin approved, visible to all
```

---

## Publication-Aware Queries

### Filtering Published Data Only

```python
# File: shared/airtable_connection.py

def get_balance_sheet_data_by_period(
    self,
    company_name: str,
    period: str
) -> list:
    """
    Get balance sheet data for company/period.
    Only returns PUBLISHED or LEGACY (blank status) data.
    """
    # Filter formula for published data only
    filter_formula = (
        f"AND("
        f"{{company}}='{company_name}',"
        f"{{period}}='{period}',"
        f"OR("
        f"{{publication_status}}='published',"
        f"{{publication_status}}=BLANK()"
        f")"
        f")"
    )

    response = self.balance_sheet_table.all(formula=filter_formula)
    return [r['fields'] for r in response]
```

### Visual Representation

```
Database Records:
┌────────────┬─────────────┬────────────────────┐
│  Company   │   Period    │ publication_status │
├────────────┼─────────────┼────────────────────┤
│ Ace        │ 2024 Annual │ published          │  ← Visible
│ Ace        │ 2024 Annual │ submitted          │  ← Hidden
│ Baker      │ 2024 Annual │ (blank)            │  ← Visible (legacy)
│ Baker      │ 2023 Annual │ published          │  ← Visible
│ Cole       │ 2024 Annual │ submitted          │  ← Hidden
└────────────┴─────────────┴────────────────────┘

Dashboard Query Result:
├── Ace - 2024 Annual (published)
├── Baker - 2024 Annual (blank/legacy)
└── Baker - 2023 Annual (published)
```

---

## Admin Publication UI

### Pending Submissions View

```python
# File: pages/admin/user_management.py (Publish Data tab)

def render_publish_data_tab():
    """Render publication control interface for super admins."""
    from shared.auth_utils import is_super_admin

    if not is_super_admin():
        st.error("Super admin access required")
        return

    st.subheader("Pending Data Submissions")

    # Get pending financial data
    pending_financial = get_pending_data_submissions()

    # Get pending W&C data
    pending_wc = get_pending_wc_submissions()

    if not pending_financial and not pending_wc:
        st.success("No pending submissions!")
        return

    # Display pending by period
    st.markdown("### Financial Data")

    for period, companies in pending_financial.items():
        with st.expander(f"📊 {period}", expanded=True):
            for company, details in companies.items():
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.write(f"**{company}**")

                with col2:
                    icons = []
                    if details.get('has_bs'):
                        icons.append("📋 BS")
                    if details.get('has_is'):
                        icons.append("📈 IS")
                    st.write(" | ".join(icons))

                with col3:
                    submitted_by = details.get('submitted_by', 'Unknown')
                    submitted_date = details.get('submitted_date', '')
                    st.caption(f"By: {submitted_by}")
                    st.caption(f"On: {submitted_date}")

            # Bulk publish button
            if st.button(f"Publish All for {period}", key=f"pub_{period}"):
                with st.spinner("Publishing..."):
                    result = publish_all_data_for_period(period)
                    st.success(
                        f"Published: {result['bs_published']} BS, "
                        f"{result['is_published']} IS records"
                    )
                    st.rerun()

    # W&C section
    st.markdown("### Wins & Challenges")

    for period, counts in pending_wc.items():
        with st.expander(f"🏆 {period}"):
            st.write(f"- {counts['wins_count']} Wins")
            st.write(f"- {counts['challenges_count']} Challenges")
            st.write(f"- {counts['action_items_count']} Action Items")

            if st.button(f"Publish W&C for {period}", key=f"pub_wc_{period}"):
                with st.spinner("Publishing..."):
                    publish_all_wc_for_period(period)
                    st.success("W&C published successfully!")
                    st.rerun()
```

---

## Getting Pending Submissions

```python
# File: shared/airtable_connection.py

def get_pending_data_submissions(self) -> dict:
    """
    Get all submitted (unpublished) financial data.

    Returns:
        Dict of period -> company -> {has_bs, has_is, submitted_by, submitted_date}
    """
    pending = {}

    # Query balance sheet for submitted status
    bs_submitted = self.balance_sheet_table.all(
        formula="{publication_status}='submitted'"
    )

    for record in bs_submitted:
        fields = record['fields']
        period = fields.get('period_name', 'Unknown')
        company = fields.get('company', 'Unknown')

        if period not in pending:
            pending[period] = {}

        if company not in pending[period]:
            pending[period][company] = {
                'has_bs': False,
                'has_is': False,
                'submitted_by': None,
                'submitted_date': None
            }

        pending[period][company]['has_bs'] = True
        pending[period][company]['submitted_by'] = fields.get('submitted_by')
        pending[period][company]['submitted_date'] = fields.get('submitted_date')

    # Query income statement for submitted status
    is_submitted = self.income_statement_table.all(
        formula="{publication_status}='submitted'"
    )

    for record in is_submitted:
        fields = record['fields']
        period = fields.get('period_name', 'Unknown')
        company = fields.get('company', 'Unknown')

        if period not in pending:
            pending[period] = {}

        if company not in pending[period]:
            pending[period][company] = {
                'has_bs': False,
                'has_is': False,
                'submitted_by': None,
                'submitted_date': None
            }

        pending[period][company]['has_is'] = True

        # Use IS submission info if BS not present
        if not pending[period][company]['submitted_by']:
            pending[period][company]['submitted_by'] = fields.get('submitted_by')
            pending[period][company]['submitted_date'] = fields.get('submitted_date')

    return pending
```

---

## Bulk Publication

### Publishing Financial Data

```python
def publish_all_data_for_period(self, period_name: str) -> dict:
    """
    Publish all submitted data for a period.

    Args:
        period_name: Period to publish (e.g., "2024 Annual")

    Returns:
        Dict with counts: {bs_published, is_published}
    """
    result = {'bs_published': 0, 'is_published': 0}

    # Get all submitted balance sheet records for period
    bs_records = self.balance_sheet_table.all(
        formula=f"AND({{period_name}}='{period_name}',{{publication_status}}='submitted')"
    )

    # Batch update to 'published'
    if bs_records:
        updates = [
            {'id': r['id'], 'fields': {'publication_status': 'published'}}
            for r in bs_records
        ]
        self.balance_sheet_table.batch_update(updates)
        result['bs_published'] = len(updates)

    # Get all submitted income statement records for period
    is_records = self.income_statement_table.all(
        formula=f"AND({{period_name}}='{period_name}',{{publication_status}}='submitted')"
    )

    # Batch update to 'published'
    if is_records:
        updates = [
            {'id': r['id'], 'fields': {'publication_status': 'published'}}
            for r in is_records
        ]
        self.income_statement_table.batch_update(updates)
        result['is_published'] = len(updates)

    return result
```

### Publishing Wins & Challenges

```python
def publish_all_wc_for_period(self, period_name: str) -> dict:
    """
    Publish all draft W&C for a period.

    Args:
        period_name: Period to publish

    Returns:
        Dict with counts
    """
    result = {'wins': 0, 'challenges': 0, 'action_items': 0}

    # Get period ID
    period_id = self._get_period_id_by_name(period_name)

    if not period_id:
        return result

    # Publish wins
    draft_wins = self.wins_table.all(
        formula=f"AND({{period}}='{period_id}',{{status}}='draft')"
    )
    if draft_wins:
        updates = [
            {'id': r['id'], 'fields': {'status': 'published'}}
            for r in draft_wins
        ]
        self.wins_table.batch_update(updates)
        result['wins'] = len(updates)

    # Publish challenges
    draft_challenges = self.challenges_table.all(
        formula=f"AND({{period}}='{period_id}',{{status}}='draft')"
    )
    if draft_challenges:
        updates = [
            {'id': r['id'], 'fields': {'status': 'published'}}
            for r in draft_challenges
        ]
        self.challenges_table.batch_update(updates)
        result['challenges'] = len(updates)

    # Publish action items
    draft_actions = self.action_items_table.all(
        formula=f"AND({{period}}='{period_id}',{{status}}='draft')"
    )
    if draft_actions:
        updates = [
            {'id': r['id'], 'fields': {'status': 'published'}}
            for r in draft_actions
        ]
        self.action_items_table.batch_update(updates)
        result['action_items'] = len(updates)

    return result
```

---

## Submission Tracking

### Recording Submission Metadata

```python
# In data_uploader.py when uploading

def upload_balance_sheet_to_airtable(
    company_name: str,
    period_name: str,
    data: dict
) -> tuple[bool, str]:
    """Upload with submission tracking."""

    from shared.auth_utils import get_user_email
    from datetime import datetime

    # Add submission metadata
    record = {
        **data,
        'company': company_name,
        'period': [period_id],
        'publication_status': 'submitted',

        # Tracking fields
        'submitted_by': get_user_email(),
        'submitted_date': datetime.now().isoformat(),
    }

    # Create or update...
```

---

## Access Control Matrix

```
┌─────────────────────┬──────────────────┬──────────────────┬────────────────┐
│     Action          │   Company User   │   Super Admin    │   Public       │
├─────────────────────┼──────────────────┼──────────────────┼────────────────┤
│ View published data │       ✅         │       ✅         │      ❌        │
│ View draft data     │       ❌         │       ✅         │      ❌        │
│ Upload data         │    ✅ (own co)   │    ✅ (all)      │      ❌        │
│ Publish data        │       ❌         │       ✅         │      ❌        │
│ View pending list   │       ❌         │       ✅         │      ❌        │
└─────────────────────┴──────────────────┴──────────────────┴────────────────┘
```

---

## Key Takeaways

- **Two status patterns**: `publication_status` for financial data, `status` for W&C
- **Query filtering** ensures only published data shows on dashboard
- **Blank status = visible** for backwards compatibility with legacy data
- **Batch updates** are more efficient than individual record updates
- **Submission metadata** provides audit trail (who submitted, when)
- **Admin-only publication** gives control over what users see

---

## Practice Exercise

**Challenge:** Add a "Reject" feature for submitted data

**Requirements:**
- Add "Reject" button next to "Publish" in admin UI
- Rejection should set status to 'rejected'
- Rejected data should be hidden from dashboard
- Send email notification to submitter
- Allow re-submission after rejection

<details>
<summary>Show Solution Approach</summary>

```python
def reject_submission(record_id: str, table_name: str, reason: str):
    """Reject a submitted record."""
    from shared.airtable_connection import AirtableConnection
    from shared.email_notifications import send_rejection_email

    airtable = AirtableConnection()

    # Get record to find submitter
    if table_name == 'balance_sheet':
        table = airtable.balance_sheet_table
    else:
        table = airtable.income_statement_table

    record = table.get(record_id)
    submitter_email = record['fields'].get('submitted_by')

    # Update status to rejected
    table.update(record_id, {
        'publication_status': 'rejected',
        'rejection_reason': reason,
        'rejected_date': datetime.now().isoformat()
    })

    # Send notification
    if submitter_email:
        send_rejection_email(
            to_email=submitter_email,
            period=record['fields'].get('period_name'),
            reason=reason
        )

    return True
```

</details>

---

## Related Topics

- **[authentication-security.md](authentication-security.md)** - Role-based access control
- **[excel-upload-system.md](excel-upload-system.md)** - How data gets submitted
- **[01-airtable-integration.md](../01-airtable-integration.md)** - Airtable query patterns

---

*You now understand the complete publication control system!*
