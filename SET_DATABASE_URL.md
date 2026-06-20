# 🔧 How to Set DATABASE_URL on Render

## Problem
Your app is trying to connect to `localhost` because `DATABASE_URL` environment variable is not set.

## Solution: Set DATABASE_URL Manually

### Step 1: Get Your PostgreSQL Database URL

1. Go to Render Dashboard: https://dashboard.render.com
2. Click on your **PostgreSQL database** (e.g., "dwaraka-mess-db")
3. Find the **"Internal Database URL"** section
4. Click **"Copy"** to copy the URL

The URL looks like:
```
postgresql://user:password@host:5432/database_name
```

**IMPORTANT:** Use **Internal** Database URL, not External!

---

### Step 2: Add DATABASE_URL to Web Service

1. Go back to Render Dashboard
2. Click on your **Web Service** (e.g., "dwaraka-mess")
3. Click **"Environment"** tab on the left
4. Click **"Add Environment Variable"**
5. Fill in:
   - **Key:** `DATABASE_URL`
   - **Value:** [Paste the Internal Database URL you copied]
6. Click **"Save Changes"**

---

### Step 3: Redeploy

Render will automatically redeploy after you save environment variables.

Watch the logs - you should now see:
```
✅ DATABASE_URL present: True
🗄️  Creating database tables...
✅ Database tables created
✅ Admin user created
🚀 Application ready to serve requests!
```

---

## Alternative: Use Blueprint Deployment

If you want automatic database connection, use Blueprint:

1. **Delete current services** (Web Service and Database) from Render
2. Go to Dashboard → **New** → **Blueprint**
3. Connect GitHub repository: `p-venkatesh2005/D_mess`
4. Render will detect `render.yaml`
5. Click **"Apply"**

Blueprint automatically:
- Creates PostgreSQL database
- Creates Web Service
- **Connects DATABASE_URL automatically**
- Sets all environment variables

---

## Check If DATABASE_URL Is Set

After setting, verify in Render Dashboard → Web Service → Environment:

You should see:
```
DATABASE_URL = postgresql://user:****@host:5432/dwaraka_mess
```

(Password will be hidden with ****)

---

## Common Mistakes

### ❌ Using External Database URL
External URL is for connecting from outside Render.
Use **Internal** URL for Render services.

### ❌ Wrong Format
Ensure URL starts with `postgresql://` (not `postgres://`)
The app will auto-fix this, but better to start correct.

### ❌ Typo in Key Name
Must be exactly: `DATABASE_URL` (all caps, underscore)

---

## After DATABASE_URL Is Set

Your deployment will succeed with:
1. ✅ Python 3.11 loads
2. ✅ Dependencies install
3. ✅ DATABASE_URL found
4. ✅ Database connection successful
5. ✅ Tables created
6. ✅ Admin user created
7. ✅ App starts on PORT

---

## If You Don't Have a Database Yet

### Create PostgreSQL Database on Render

1. Dashboard → **New** → **PostgreSQL**
2. Settings:
   - **Name:** dwaraka-mess-db
   - **Database:** dwaraka_mess
   - **Region:** Oregon (same as web service)
   - **Plan:** Free
3. Click **"Create Database"**
4. Wait 1-2 minutes for provisioning
5. Copy **Internal Database URL**
6. Follow "Step 2" above to add to Web Service

---

## Need Help?

If DATABASE_URL is set but still fails, share:
1. Screenshot of Environment Variables (hide password)
2. Complete error message from logs
3. First 20 lines of deployment logs

The error will tell us exactly what's wrong!
