# Setup Admin User - Quick Guide

## Problem
If you're getting "Incorrect username or password" even with correct credentials, the admin user might not exist in the database.

## Solution: Create Admin User

### Step 1: Run the Admin Creation Script

Open a terminal in the project root and run:

```bash
python scripts/create_admin.py
```

This will:
- Connect to MongoDB
- Check if admin user exists
- Create admin user if it doesn't exist

### Step 2: Verify Admin User Created

You should see output like:
```
✅ Admin user created successfully!
==================================================
ADMIN CREDENTIALS:
==================================================
Username: admin
Email: admin@moveinsync.com
Password: Admin123!
Role: ADMIN
==================================================
```

### Step 3: Login

Now you can login with:
- **Username:** `admin`
- **Password:** `Admin123!`

## Alternative: Register a New User

If you prefer, you can also register a new user via the API:

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@moveinsync.com",
    "password": "Admin123!",
    "full_name": "System Administrator",
    "role": "ADMIN"
  }'
```

## Troubleshooting

### MongoDB Connection Issues
Make sure MongoDB is running:
```bash
# Check if MongoDB is running
# Windows: Check Services
# Linux/Mac: sudo systemctl status mongod
```

### Database Connection String
Check your `.env` file has the correct MongoDB connection string:
```
MONGODB_URL=mongodb://localhost:27017/alert_management
```

### User Already Exists
If the script says "Admin user already exists", try:
1. Check the password is correct: `Admin123!`
2. Verify the user is active in the database
3. Try resetting the password (you may need to delete and recreate the user)

## Quick Test

After creating the admin user, test login:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'
```

You should get a JWT token in response.

