# 🔑 Create Admin User - Step by Step

## Problem
"No account found with that phone number" when trying to login as admin.

## Solution
The admin user needs to be created in your Neon database.

---

## 🎯 **Option 1: Run via Render Shell (Easiest)**

### Step 1: Open Render Shell
1. Go to Render Dashboard: https://dashboard.render.com
2. Click your **Web Service** (dwaraka-mess)
3. Click **"Shell"** tab in the top menu
4. Wait for shell to connect

### Step 2: Run Admin Creation Script
In the shell, type:

```bash
python create_admin.py
```

### Step 3: Check Output
You should see:
```
✅ Admin user created successfully!
📱 Phone:    9999999999
🔑 Password: admin123 (or your ADMIN_PASSWORD value)
```

### Step 4: Login
- Go to your app URL
- Phone: `9999999999`
- Password: Check the output or your `ADMIN_PASSWORD` env var

---

## 🎯 **Option 2: Run SQL Directly in Neon Console**

### If Render shell doesn't work, use Neon:

1. **Go to Neon Console:** https://console.neon.tech
2. **Click SQL Editor**
3. **Run this SQL:**

```sql
-- Create admin user
INSERT INTO users (name, phone, email, role, password_hash, created_at)
VALUES (
    'Dwaraka Admin',
    '9999999999',
    'admin@dwaraka.com',
    'admin',
    'scrypt:32768:8:1$<hash_will_be_generated>',
    CURRENT_TIMESTAMP
);
```

**Wait!** You need the password hash. Let me give you the Python command to generate it:

### Step 2.1: Generate Password Hash

In Render Shell or locally:

```python
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
```

This will output something like:
```
scrypt:32768:8:1$abc123xyz...
```

### Step 2.2: Use the Hash in SQL

```sql
INSERT INTO users (name, phone, email, role, password_hash, created_at)
VALUES (
    'Dwaraka Admin',
    '9999999999',
    'admin@dwaraka.com',
    'admin',
    'scrypt:32768:8:1$YOUR_HASH_HERE',  -- Replace with generated hash
    CURRENT_TIMESTAMP
);
```

---

## 🎯 **Option 3: Run Locally Then Check**

### If you have Neon connection string:

1. **On your computer, set DATABASE_URL:**

   **Windows CMD:**
   ```cmd
   set DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
   ```

   **Windows PowerShell:**
   ```powershell
   $env:DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require"
   ```

   **Mac/Linux:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require"
   ```

2. **Run the script:**
   ```bash
   python create_admin.py
   ```

3. **Admin created in Neon database!**

---

## 🎯 **Option 4: Update wsgi.py to Force Admin Creation**

Let me create a version that's more aggressive about creating admin:

### Updated wsgi.py (I'll commit this):

```python
# Always try to create admin on startup
with app.app_context():
    try:
        db.create_all()
        
        # Force check and create admin
        admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
        admin = User.query.filter_by(phone=admin_phone).first()
        
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin = User(name='Dwaraka Admin', phone=admin_phone, 
                        email='admin@dwaraka.com', role='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ ADMIN CREATED: Phone {admin_phone}")
    except Exception as e:
        print(f"Admin creation error: {e}")
```

---

## ✅ **Verify Admin Exists**

### Check in Neon SQL Editor:

```sql
-- Check if admin exists
SELECT id, name, phone, email, role, created_at 
FROM users 
WHERE role = 'admin';
```

Should return:
```
id | name          | phone       | email              | role  | created_at
1  | Dwaraka Admin | 9999999999  | admin@dwaraka.com  | admin | 2026-06-20...
```

---

## 🔧 **Troubleshooting**

### Error: "relation 'users' does not exist"
**Cause:** Tables not created yet

**Fix:**
```bash
# In Render Shell
python -c "from app import create_app; from extensions import db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created!')"
```

### Error: "duplicate key value violates unique constraint"
**Cause:** Admin already exists

**Fix:**
```sql
-- Check existing admin
SELECT * FROM users WHERE phone = '9999999999';

-- Reset password (get hash from Python first)
UPDATE users 
SET password_hash = 'scrypt:32768:8:1$YOUR_NEW_HASH'
WHERE phone = '9999999999';
```

### Error: "Connection refused"
**Cause:** DATABASE_URL not set in Render

**Fix:** Add DATABASE_URL to Render Environment variables

---

## 🚀 **Quick Fix - Run This Now:**

### In Render Shell (Fastest):

```bash
python create_admin.py
```

**OR if that fails:**

```bash
python << 'EOF'
from app import create_app
from extensions import db
from models import User
import os

app = create_app()
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(phone='9999999999').first()
    if not admin:
        admin = User(name='Admin', phone='9999999999', email='admin@dwaraka.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created!")
    else:
        print("Admin exists!")
EOF
```

---

## 📞 **After Creating Admin:**

**Login with:**
- Phone: `9999999999`
- Password: `admin123` (or your ADMIN_PASSWORD value)

**Then immediately:**
1. Go to profile settings
2. Change password to something secure
3. Update email if needed

---

**Try Option 1 (Render Shell) first - it's the easiest!**
