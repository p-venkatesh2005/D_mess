# Docker Setup for Windows - Dwaraka Mess System

## Step 1: Install Docker Desktop

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - File size: ~500MB

2. **Install:**
   - Run the installer
   - Accept defaults (Enable WSL 2 if prompted)
   - Restart computer when asked

3. **Start Docker Desktop:**
   - Open Docker Desktop from Start Menu
   - Wait for "Docker Desktop is running" (green indicator in system tray)
   - First start takes 2-3 minutes

## Step 2: Verify Installation

Open PowerShell and run:
```powershell
docker --version
docker-compose --version
```

You should see version numbers.

## Step 3: Setup Environment

```powershell
cd c:\Users\venka\Downloads\D_mess-main\D_mess-main
copy .env.example .env
```

## Step 4: Start Services

```powershell
docker-compose up -d
```

This will:
- Download PostgreSQL image (~2 minutes)
- Build Flask app image (~3 minutes)
- Start both containers
- Create database

## Step 5: Initialize Database

Wait 15 seconds after step 4, then:
```powershell
docker exec -it dwaraka_mess_app python init_db.py
```

## Step 6: Access Application

Open browser: **http://localhost:5000**

**Login Credentials:**
- Admin: Phone `9999999999` | Password `admin123`
- Student: Phone `8111111111` | Password `student123`

## Useful Commands

```powershell
# View logs
docker-compose logs -f app
docker-compose logs -f postgres

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check status
docker-compose ps

# Access PostgreSQL directly
docker exec -it dwaraka_mess_db psql -U postgres -d dwaraka_mess
```

## Troubleshooting

**Docker Desktop won't start:**
- Enable virtualization in BIOS
- Enable WSL 2: `wsl --install`

**Port 5000 already in use:**
- Change in docker-compose.yml: `"5001:5000"`
- Access at http://localhost:5001

**Container won't start:**
```powershell
docker-compose down -v
docker-compose up --build -d
```

## Next Steps After Docker Installation

Once Docker is installed and running, come back and run:
```powershell
cd c:\Users\venka\Downloads\D_mess-main\D_mess-main
.\scripts\docker-quick-start.bat
```
