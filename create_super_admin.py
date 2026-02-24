"""
BPC Dashboard - Create Super Admin User
=======================================
This script creates the first super admin user for the BPC Dashboard.

Usage:
    python create_super_admin.py

The script will prompt you for:
- Email address
- Password
- Full name

IMPORTANT: Run this script ONCE to create your first super admin account.
After that, you can create additional users through the web interface.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from getpass import getpass

def create_super_admin():
    """Create the first super admin user"""

    print("=" * 70)
    print("BPC DASHBOARD - CREATE SUPER ADMIN USER")
    print("=" * 70)
    print()

    # Load environment variables
    print("📋 Loading environment variables...")
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_service_key:
        print("❌ ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env file")
        print("   Please make sure your .env file is configured correctly.")
        return False

    print("✅ Environment variables loaded")
    print()

    # Create Supabase admin client
    print("🔌 Connecting to Supabase...")
    try:
        supabase: Client = create_client(supabase_url, supabase_service_key)
        print("✅ Connected to Supabase")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Supabase: {e}")
        return False

    # Collect user information
    print("👤 Enter super admin details:")
    print()

    email = input("Email address: ").strip()
    if not email or '@' not in email:
        print("❌ ERROR: Invalid email address")
        return False

    password = getpass("Password (min 6 characters): ")
    if len(password) < 6:
        print("❌ ERROR: Password must be at least 6 characters")
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ ERROR: Passwords do not match")
        return False

    full_name = input("Full name: ").strip()
    if not full_name:
        print("❌ ERROR: Full name is required")
        return False

    print()
    print("Creating super admin user...")
    print(f"  Email: {email}")
    print(f"  Name: {full_name}")
    print(f"  Role: super_admin")
    print()

    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return False

    print()
    print("🔄 Creating user in Supabase Auth...")

    try:
        # Step 1: Create user in Supabase Auth
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True  # Auto-confirm email for first admin
        })

        user_id = auth_response.user.id
        print(f"✅ User created in Auth (ID: {user_id})")
        print()

        # Step 2: Create user profile
        print("🔄 Creating user profile...")
        profile_response = supabase.table('user_profiles').insert({
            'id': user_id,
            'full_name': full_name,
            'role': 'super_admin',
            'company_id': None,  # Super admins are not assigned to a specific company
            'can_upload_data': True,
            'is_active': True
        }).execute()

        print("✅ User profile created")
        print()

        # Step 3: Log the creation in audit logs
        print("🔄 Logging audit event...")
        supabase.table('audit_logs').insert({
            'user_id': user_id,
            'action': 'create_user',
            'resource': 'users',
            'metadata': {
                'created_role': 'super_admin',
                'created_email': email,
                'created_by': 'setup_script'
            }
        }).execute()

        print("✅ Audit log created")
        print()

        # Success!
        print("=" * 70)
        print("✅ SUCCESS! Super admin user created!")
        print("=" * 70)
        print()
        print("📧 Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: (the one you just entered)")
        print()
        print("🎉 Next steps:")
        print("   1. Run: streamlit run financial_dashboard.py")
        print("   2. You should see the login page")
        print("   3. Enter your email and password")
        print("   4. You're in! Create more users from the admin panel.")
        print()

        return True

    except Exception as e:
        print(f"❌ ERROR: Failed to create user: {e}")
        print()
        print("Possible reasons:")
        print("  - User with this email already exists")
        print("  - Database tables not set up correctly (run database_setup.sql first)")
        print("  - Invalid Supabase credentials")
        print()
        return False


if __name__ == "__main__":
    success = create_super_admin()

    if not success:
        print()
        print("=" * 70)
        print("❌ FAILED TO CREATE SUPER ADMIN")
        print("=" * 70)
        print()
        print("Troubleshooting:")
        print("  1. Make sure database_setup.sql has been run in Supabase")
        print("  2. Check that .env file has correct SUPABASE_URL and SUPABASE_SERVICE_KEY")
        print("  3. Verify your Supabase project is active")
        print("  4. Check that this email doesn't already exist in Supabase")
        print()
        exit(1)
    else:
        exit(0)
