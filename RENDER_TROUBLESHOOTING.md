# 🔧 Render Deployment Troubleshooting

## Recent Fix Applied ✅

**Issue:** Build was failing because `init_db_safe.py` tried to connect to database during build phase.

**Solution:** 
- Build script now only installs dependencies and creates directories
- Database initialization happens automatically on first app startup in `wsgi.py`
- No database connection needed during build phase

---

## How to Check Render Logs

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on your service (e.g., "dwaraka-mess")
3. Click "Logs" tab
4. Look for error messages (usually in red)

---

## Common Deployment Errors & Solutions

### 1. Build Phase Errors

#### Error: "Permission denied: ./build.sh"
**Status:** ✅ FIXED
- build.sh is now executable in git

#### Error: "pip: command not found"
**Solution:** Render should have Python pre-installed
- Check that Runtime is set to "Python 3"
- Python version: 3.11.0 (set in render.yaml)

#### Error: "No module named 'X'"
**Solution:** Missing dependency in requirements.txt
- Check if the module is listed in requirements.txt
- Try adding the specific version
- Ensure requirements.txt has no typos

---

### 2. Database Connection Errors

#### Error: "could not connect to server"
**Possible Causes:**
1. DATABASE_URL not set
2. Database not created yet
3. Wrong DATABASE_URL format

**Solution:**
```bash
# In Render Dashboard → Web Service → Environment
# Make sure DATABASE_URL is set and points to your PostgreSQL database

# If using Blueprint (render.yaml):
# - Database should auto-create
# - DATABASE_URL should auto-link

# If manual setup:
# - Create PostgreSQL database first
# - Copy Internal Database URL
# - Add as DATABASE_URL environment variable
```

#### Error: "database 'dwaraka_mess' does not exist"
**Solution:**
- Create database manually in PostgreSQL dashboard
- Or use the database name that Render created
- Update DATABASE_URL if needed

---

### 3. Application Startup Errors

#### Error: "gunicorn: command not found"
**Solution:** gunicorn should be in requirements.txt
```
gunicorn==22.0.0
```

#### Error: "No module named 'app'"
**Solution:** Check file structure
- wsgi.py should exist in root
- app.py should exist in root
- All blueprint files should be in blueprints/

#### Error: "Address already in use"
**Solution:** Render manages the PORT automatically
- Don't hardcode port in start command
- Use `$PORT` environment variable
- Start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

---

### 4. Runtime Errors

#### Error: "Application failed to respond"
**Causes:**
1. App is taking too long to start
2. App crashed immediately
3. Wrong PORT binding

**Solution:**
- Check logs for Python errors
- Ensure gunicorn is binding to `0.0.0.0:$PORT`
- Increase worker timeout if needed

#### Error: "Worker timeout"
**Solution:** Increase timeout in start command
```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

---

## Verification Checklist

After deployment, verify:

### ✅ Build Phase
- [ ] Dependencies installed successfully
- [ ] No Python errors during pip install
- [ ] Build completes without errors
- [ ] "Build complete!" message appears

### ✅ Deploy Phase  
- [ ] Gunicorn starts successfully
- [ ] No "Address in use" errors
- [ ] Workers initialize properly
- [ ] "Booting worker" messages appear

### ✅ Application Health
- [ ] App responds to HTTP requests
- [ ] Home page loads (https://your-app.onrender.com)
- [ ] No 500 errors
- [ ] Admin login page accessible

### ✅ Database
- [ ] Tables created automatically
- [ ] Admin user created
- [ ] Can login with admin credentials
- [ ] Database operations work

---

## Manual Database Check

If you need to manually verify database:

1. **Open Render Shell** (Dashboard → Web Service → Shell)

2. **Check if admin exists:**
```python
python
from app import create_app
from models import User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(role='admin').first()
    if admin:
        print(f"Admin exists: {admin.phone}")
    else:
        print("No admin found")
```

3. **Manually create admin if needed:**
```python
python
from app import create_app
from extensions import db
from models import User
app = create_app()
with app.app_context():
    admin = User(name='Admin', phone='9999999999', email='admin@dwaraka.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Admin created!")
```

---

## Environment Variables to Check

In Render Dashboard → Environment tab, verify:

```bash
# Required
DATABASE_URL=postgresql://...  # Should be auto-set
SECRET_KEY=...                 # Should be auto-generated
FLASK_ENV=production

# Admin
ADMIN_PHONE=9999999999
ADMIN_PASSWORD=...             # Auto-generated or set manually

# Optional (with defaults)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
PYTHON_VERSION=3.11.0
```

---

## If All Else Fails

### Option 1: Manual Web Service Setup

Instead of Blueprint, create manually:

1. **Create PostgreSQL Database**
   - Name: dwaraka-mess-db
   - Database: dwaraka_mess
   - Copy Internal Database URL

2. **Create Web Service**
   - Repository: p-venkatesh2005/D_mess
   - Build Command: `./build.sh`
   - Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

3. **Set Environment Variables** (see list above)

### Option 2: Deploy to Heroku Instead

If Render keeps failing:

1. **Install Heroku CLI**
2. **Login:** `heroku login`
3. **Create app:** `heroku create dwaraka-mess`
4. **Add PostgreSQL:** `heroku addons:create heroku-postgresql:essential-0`
5. **Set config:** `heroku config:set ADMIN_PHONE=9999999999`
6. **Deploy:** `git push heroku main`

Procfile is already configured for Heroku!

### Option 3: Use Railway

Railway is similar to Render:

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select repository
4. Add PostgreSQL database
5. Railway auto-detects Python and requirements.txt
6. Set environment variables
7. Deploy!

---

## Getting Help

1. **Share Exact Error Message**
   - Copy from Render logs
   - Include full stack trace
   - Note which phase failed (build/deploy/runtime)

2. **Check Render Status**
   - https://status.render.com
   - Outages might affect deployment

3. **Render Community**
   - https://community.render.com
   - Search for similar issues

4. **Contact Render Support**
   - Dashboard → Help → Contact Support
   - Include service name and error logs

---

## Current Configuration Summary

Your app is configured with:

- **Runtime:** Python 3.11
- **Web Server:** Gunicorn (2 workers, 120s timeout)
- **Database:** PostgreSQL 16
- **Build:** Automated via build.sh
- **Deployment:** Continuous from GitHub main branch
- **Database Init:** Automatic on first app startup (wsgi.py)

**This should work!** If you're still seeing errors, please share the exact error message from Render logs.
