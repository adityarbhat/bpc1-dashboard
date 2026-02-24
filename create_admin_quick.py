#!/usr/bin/env python3
"""
Quick script to create a super admin user
"""

from dotenv import load_dotenv
import os
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# User credentials
EMAIL = "adi@imaiconsultants.com"
PASSWORD = "Admin123!"
FULL_NAME = "Aditya Bhat"

def create_super_admin():
    """Create super admin user"""

    print(f"Creating super admin: {EMAIL}")

    # Create Supabase admin client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    try:
        # Create user in Supabase Auth
        print("Creating user in Supabase Auth...")
        auth_response = supabase.auth.admin.create_user({
            "email": EMAIL,
            "password": PASSWORD,
            "email_confirm": True
        })

        user_id = auth_response.user.id
        print(f"✅ User created in Auth with ID: {user_id}")

        # Create user profile
        print("Creating user profile...")
        profile_data = {
            "id": user_id,
            "full_name": FULL_NAME,
            "role": "super_admin",
            "company_id": None,
            "can_upload_data": True,
            "is_active": True
        }

        supabase.table('user_profiles').insert(profile_data).execute()
        print("✅ User profile created")

        print(f"""
✅ Super admin created successfully!

Login credentials:
Email: {EMAIL}
Password: {PASSWORD}

You can now log in to the dashboard.
        """)

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    create_super_admin()
