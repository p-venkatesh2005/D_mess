# 🔓 Activate Admin Account - QUICK FIX

## Problem
"Your account has been deactivated" when logging in as admin.

The admin user exists but `is_active=False`.

---

## ✅ **INSTANT FIX - Run This SQL in Neon**

### Step 1: Go to Neon SQL Editor
https://console.neon.tech → Your Project → SQL Editor

### Step 2: Run This Command

```sql
-- Activate admin account
UPDATE users 
SET is_active = true 
WHERE phone = '9999999999' AND role = 'admin';
```

### Step 3: Verify

```sql
-- Check admin status
SELECT id, name, phone, role, is_active 
FROM users 
WHERE phone = '9999999999';
```

Should show:
```
id | name          | phone       | role  | is_active
1  | Dwaraka Admin | 9999999999  | admin | true
```

### Step 4: Login Again
- Go to your app
- Phone: `9999999999`
- Password: `admin123` (or your ADMIN_PASSWORD)
- ✅ Should work now!

---

## 🔧 **Alternative: Use Render Shell**

### Option A: Rerun create_admin.py
```bash
# In Render Shell
python create_admin.py
```
When prompted "Do you want to reset password and reactivate? (y/n):", type `y`

### Option B: Direct Python Command
```bash
# In Render Shell
python << 'EOF'
from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(phone='9999999999').first()
    if admin:
        admin.is_active = True
        db.session.commit()
        print(f"✅ Admin activated! Phone: {admin.phone}")
    else:
        print("❌ Admin not found")
EOF
```

---

## 🔍 **Why Did This Happen?**

Possible causes:
1. Admin was created with `is_active=False` by mistake
2. Admin was manually deactivated in database
3. Some initialization script set wrong default

**Now fixed:** 
- `create_admin.py` explicitly sets `is_active=True`
- `wsgi.py` checks and reactivates on startup

---

## 🚀 **After Activation:**

1. **Login works** ✅
2. **Access admin dashboard** ✅
3. **Change password** (recommended)
4. **Start managing students** ✅

---

## 📝 **For Future Reference:**

### Check Any User's Status:
```sql
SELECT id, name, phone, role, is_active 
FROM users;
```

### Deactivate a User (if needed):
```sql
UPDATE users SET is_active = false WHERE phone = '8111111111';
```

### Reactivate a User:
```sql
UPDATE users SET is_active = true WHERE phone = '8111111111';
```

---

## ⚡ **QUICKEST FIX:**

**Just run this SQL in Neon now:**
```sql
UPDATE users SET is_active = true WHERE phone = '9999999999';
```

**Then login immediately!** 🎉
