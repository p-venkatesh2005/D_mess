# 🚀 Render Deployment Guide - Dwaraka Mess Management System

## Quick Deploy (Automatic)

1. **Push Code to GitHub** (Already done ✅)
   ```bash
   git push origin main
   ```

2. **Deploy on Render**
   - Go to: https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository: `p-venkatesh2005/D_mess`
   - Render will automatically detect `render.yaml` and create:
     - PostgreSQL database (dwaraka-mess-db)
     - Web service (dwaraka-mess)

3. **Set Environment Variables** (if needed)
   - `ADMIN_PASSWORD` - Generated automatically (check dashboard)
   - `SECRET_KEY` - Generated automatically
   - All other variables are pre-configured in `render.yaml`

4. **Access Your App**
   - URL will be: `https://dwaraka-mess.onrender.com`
   - Admin Phone: `9999999999`
   - Admin Password: Check Render dashboard environment variables

---

## Manual Deploy (Step by Step)

### Step 1: Create PostgreSQL Database

1. Go to Render Dashboard → "New" → "PostgreSQL"
2. Settings:
   - Name: `dwaraka-mess-db`
   - Database: `dwaraka_mess`
   - Region: Oregon (US West)
   - Plan: Free
3. Click "Create Database"
4. **Copy the Internal Database URL** from the database info page

### Step 2: Create Web Service

1. Go to Render Dashboard → "New" → "Web Service"
2. Connect your GitHub repository: `p-venkatesh2005/D_mess`
3. Settings:
   - Name: `dwaraka-mess`
   - Region: Oregon (US West)
   - Branch: `main`
   - Runtime: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -`
   - Plan: Free

### Step 3: Environment Variables

Add these in Web Service → Environment:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this

# Database (use Internal Database URL from Step 1)
DATABASE_URL=postgresql://user:pass@host/dwaraka_mess

# Admin Credentials
ADMIN_PHONE=9999999999
ADMIN_PASSWORD=your-secure-admin-password

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800

# Python Version
PYTHON_VERSION=3.11.0
```

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for build to complete (~3-5 minutes)
3. Check logs for any errors
4. Access your app at the provided URL

---

## 🔧 Troubleshooting

### Build Fails with "Permission denied: ./build.sh"

**Solution:** Make build.sh executable
```bash
git update-index --chmod=+x build.sh
git commit -m "Make build.sh executable"
git push origin main
```

### Database Connection Error

**Issue:** `FATAL: no pg_hba.conf entry`

**Solution:** 
- Use the **Internal Database URL** (not External)
- Format: `postgresql://user:pass@internal-host/dwaraka_mess`
- Render services in the same region can connect internally

### Application Crashes on Start

**Check:**
1. View logs in Render dashboard
2. Ensure DATABASE_URL is set correctly
3. Verify all required environment variables are present
4. Check if database migration completed successfully

### "Module not found" Error

**Solution:** Ensure `requirements.txt` has all dependencies:
```bash
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Werkzeug==3.0.3
python-dotenv==1.0.1
Pillow>=10.4.0
WTForms==3.1.2
email-validator==2.1.1
gunicorn==22.0.0
qrcode[pil]>=7.4.2
openpyxl>=3.1.2
requests>=2.31.0
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
```

### Gunicorn Worker Timeout

**Solution:** Increase timeout in start command:
```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

---

## 📊 Post-Deployment Checklist

- [ ] Application loads without errors
- [ ] Admin login works (`9999999999` / your password)
- [ ] Database tables created successfully
- [ ] Student registration works
- [ ] Payment upload works
- [ ] QR code generation works
- [ ] File uploads work (static/uploads/payments)

---

## 🔒 Security Recommendations

1. **Change Default Admin Password**
   - Login as admin
   - Go to profile settings
   - Change from default password

2. **Set Strong SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   - Use this value for SECRET_KEY environment variable

3. **Enable HTTPS** (Automatic on Render)
   - All Render URLs use HTTPS by default

4. **Environment Variables**
   - Never commit `.env` files
   - Keep sensitive data in Render dashboard only

---

## 📈 Scaling on Render

### Free Tier Limitations
- Web service: Spins down after 15 min of inactivity
- Database: 1 GB storage, 100 connections
- Build minutes: 500/month

### Upgrade Options
1. **Starter Plan** ($7/month)
   - No sleep/spin down
   - More CPU & memory
   
2. **Database Plan** ($7/month)
   - 10 GB storage
   - Better performance

3. **Connection Pooling**
   - Already configured in `config.py`
   - Optimizes database connections

---

## 🔗 Useful Links

- Render Dashboard: https://dashboard.render.com
- Render Docs: https://render.com/docs
- PostgreSQL Docs: https://render.com/docs/databases
- GitHub Repo: https://github.com/p-venkatesh2005/D_mess

---

## 🆘 Support

If deployment fails:
1. Check Render logs (Dashboard → Your Service → Logs)
2. Review build output for errors
3. Verify environment variables
4. Check database connection string
5. Ensure `build.sh` is executable

**Common Log Locations:**
- Build logs: Shows pip install and migration output
- Deploy logs: Shows gunicorn startup
- Application logs: Shows Flask runtime errors
