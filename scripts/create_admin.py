"""Script to create the first admin user in the database."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import Database
from src.database.models import UserRole
from app.auth.password_utils import hash_password


async def create_admin_user():
    """
    Create the first admin user if it doesn't exist.

    Creates an admin user with:
    - username: "admin"
    - email: "admin@moveinsync.com"
    - password: "Admin123!" (hashed)
    - full_name: "System Administrator"
    - role: UserRole.ADMIN
    - is_active: True
    """
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        await Database.connect()
        print("Connected to MongoDB successfully!")

        # Get database and users collection
        database = Database.get_database()
        users_collection = database["users"]

        # Check if admin user already exists
        print("Checking if admin user exists...")
        existing_admin = await users_collection.find_one({"username": "admin"})

        if existing_admin:
            print("Admin user already exists!")
            print(f"Username: admin")
            print(f"Email: {existing_admin.get('email', 'N/A')}")
            return

        # Create admin user
        print("Creating admin user...")

        # Hash password
        password = "Admin123!"
        print(f"DEBUG: Password to be hashed (length {len(password)}): '{password}'")
    
        hashed_password = hash_password(password)

        # Create user document
        admin_user = {
            "username": "admin",
            "email": "admin@moveinsync.com",
            "hashed_password": hashed_password,
            "full_name": "System Administrator",
            "role": UserRole.ADMIN.value,
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "last_login": None,
        }

        # Insert into MongoDB
        result = await users_collection.insert_one(admin_user)
        print(f"\n✅ Admin user created successfully!")
        print("\n" + "=" * 50)
        print("ADMIN CREDENTIALS:")
        print("=" * 50)
        print(f"Username: admin")
        print(f"Email: admin@moveinsync.com")
        print(f"Password: Admin123!")
        print(f"Role: ADMIN")
        print("=" * 50)
        print("\n⚠️  IMPORTANT: Please change the password after first login!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error creating admin user: {str(e)}")
        raise
    finally:
        # Close database connection
        print("\nClosing database connection...")
        await Database.disconnect()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(create_admin_user())

