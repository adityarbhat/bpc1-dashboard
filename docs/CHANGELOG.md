# Changelog - BPC2 Dashboard

This file contains detailed implementation history moved from CLAUDE.md for reference.

## January 2026
- Professional Excel Export Formatting with color coding across 7 sheets (`shared/excel_formatter.py`)
- Centralized Export Feature with lazy loading (`shared/export_utils.py`, `pages/group_pages/group_export.py`)
- Consolidated Excel Upload with multi-sheet template (`bpc_upload_template/`)
- Authentication Security Hardening Phase 2 (XSRF/CORS, cookie validation)

## December 2025
- Ratio Table Color Coding Bug Fix (decimal threshold values in `company_ratios.py`)
- Authentication User Identity Bug Fix (removed Supabase client caching)
- Role-Based Access Control for Admin Features
- Sidebar Navigation Active State Highlighting

## November 2025
- Authentication System Implementation Phase 1 (Supabase, RLS, RBAC)
- Data Input Description Column
- Admin Pages Layout Fix

## October 2025
- Financial Glossary Page (`pages/resources/glossary_page.py`)
- Company Wins & Challenges Analysis

## September 2025
- Performance Optimization (80-90% API call reduction)
- Value Trend Analysis System

## August 2025
- Financial Gauge Charts with speedometer design
- Advanced Currency Formatting (K/M suffixes)
- Navigation Enhancements

For detailed implementation notes, see the git history or individual file docstrings.
