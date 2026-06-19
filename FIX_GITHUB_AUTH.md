# Fix GitHub Authentication Issue

## Problem
Your local Git is using the wrong GitHub account (`p-venkatesh3005` instead of `p-venkatesh2005`)

## Solution

### Option 1: Use GitHub Personal Access Token (Recommended)

#### Step 1: Create Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. **Name:** `dwaraka-mess-deployment`
4. **Expiration:** 90 days (or No expiration)
5. **Select scopes:** Check ✅ **repo** (all repository access)
6. Click **"Generate token"**
7. **COPY THE TOKEN** (you won't see it again!)

#### Step 2: Push with Token

```powershell
cd c:\Users\venka\Downloads\D_mess-main\D_mess-main

# Push using token (you'll be prompted for credentials)
git push -u origin main

# When prompted:
# Username: p-venkatesh2005
# Password: [PASTE YOUR TOKEN HERE]
```

---

### Option 2: Update Git Credentials

#### Clear Old Credentials

```powershell
# Clear Windows Credential Manager
git credential-manager uninstall
git credential-manager install

# Or use GUI: Control Panel → Credential Manager → Windows Credentials
# Remove any github.com entries
```

#### Then Push Again

```powershell
git push -u origin main
# Enter: p-venkatesh2005
# Password: [your password or token]
```

---

### Option 3: Use SSH Instead of HTTPS

#### Step 1: Generate SSH Key

```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "venkatesh2005p@gmail.com"

# Press Enter for default location
# Press Enter twice for no passphrase (or set one)

# Copy public key
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

#### Step 2: Add to GitHub

1. Go to: https://github.com/settings/keys
2. Click **"New SSH key"**
3. Title: `Windows PC - Dwaraka Mess`
4. Paste the key from above
5. Click **"Add SSH key"**

#### Step 3: Change Remote to SSH

```powershell
cd c:\Users\venka\Downloads\D_mess-main\D_mess-main

# Change remote from HTTPS to SSH
git remote remove origin
git remote add origin git@github.com:p-venkatesh2005/D_mess.git

# Push
git push -u origin main
```

---

## Quick Fix (Using Token)

**Fastest solution - Copy and run these:**

1. **Create token:** https://github.com/settings/tokens/new
   - Name: `dwaraka-mess`
   - Scope: ✅ repo
   - Click Generate

2. **Copy token and run:**

```powershell
cd c:\Users\venka\Downloads\D_mess-main\D_mess-main

# This will prompt for credentials
git push -u origin main

# Enter:
# Username: p-venkatesh2005
# Password: [PASTE TOKEN HERE - NOT YOUR PASSWORD]
```

3. **Done!** Token will be saved for future pushes.

---

## Troubleshooting

### "Permission denied"
- Make sure you're logged in as **p-venkatesh2005** not p-venkatesh3005
- Use Personal Access Token instead of password

### "Authentication failed"
- GitHub no longer accepts password authentication
- Must use Personal Access Token or SSH

### "Repository not found"
- Check repository exists: https://github.com/p-venkatesh2005/D_mess
- Check spelling in remote URL

---

## Verify After Push

After successful push, check:

```powershell
# View remote
git remote -v

# Check push status
git status

# View on GitHub
# https://github.com/p-venkatesh2005/D_mess
```

---

## Current Status

✅ Code committed locally  
✅ Remote added to GitHub  
⚠️ Authentication needed to push  

**Next:** Create Personal Access Token and push!

---

## Token Creation Direct Link

Click here: https://github.com/settings/tokens/new?scopes=repo&description=dwaraka-mess-deployment

This pre-fills the form with:
- Name: dwaraka-mess-deployment
- Scope: repo ✅

Just click "Generate token" and copy it!
