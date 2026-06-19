# ⚡ Quick Start - PostgreSQL Setup

Choose your deployment option below and follow the commands.

---

## 🐳 Option 1: Docker Compose (5 minutes) - RECOMMENDED

**Best for:** Development, testing, and small deployments

```bash
# Step 1: Setup environment
cp .env.example .env

# Step 2: Start PostgreSQL + Application
docker-compose up -d

# Step 3: Wait 10 seconds for services to start
sleep 10

# Step 4: Initialize database
docker-compose exec -it dwaraka_mess_app python init_db.py

# Step 5: Open browser
# → http://localhost:5000
```

**Login credentials:**
- Admin: Phone `9999999999` | Password `admin123`
- Student: Phone `8111111111` | Password `student123`

**Check status:**
```bash
docker-compose ps
docker-compose logs app
docker-compose logs postgres
```

**Stop services:**
```bash
docker-compose down
```

---

## 💻 Option 2: Manual Local Setup (15 minutes)

**Best for:** Development without Docker

### Windows

```bash
# 1. Install PostgreSQL
# Download from: https://www.postgresql.org/download/windows/
# During installation, remember the password you set

# 2. Open PostgreSQL command line (psql)
# Start → Programs → PostgreSQL → SQL Shell (psql)

# 3. Create database and user
postgres=# CREATE DATABASE dwaraka_mess;
postgres=# CREATE USER dwaraka_user WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=# \q

# 4. Setup Python environment
pip install -r requirements.txt

# 5. Create .env file
copy .env.example .env

# 6. Update .env
# Edit .env and change:
# DB_USER=dwaraka_user
# DB_PASSWORD=your_secure_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=dwaraka_mess

# 7. Initialize database
set FLASK_APP=app.py
set FLASK_ENV=development
flask shell
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     print('✅ Database initialized!')
>>> exit()

python init_db.py

# 8. Run application
flask run

# 9. Open browser → http://localhost:5000
```

### macOS

```bash
# 1. Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# 2. Create database and user
psql postgres
postgres=# CREATE DATABASE dwaraka_mess;
postgres=# CREATE USER dwaraka_user WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=# \q

# 3-8. Same as Linux (see below)
```

### Linux (Ubuntu/Debian)

```bash
# 1. Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 2. Create database and user
sudo -u postgres psql
postgres=# CREATE DATABASE dwaraka_mess;
postgres=# CREATE USER dwaraka_user WITH PASSWORD 'your_secure_password';
postgres=# ALTER ROLE dwaraka_user SET client_encoding TO 'utf8';
postgres=# ALTER ROLE dwaraka_user SET default_transaction_isolation TO 'read committed';
postgres=# GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=# \q

# 3. Setup Python
pip install -r requirements.txt
cp .env.example .env

# 4. Update .env
nano .env
# Change: DB_USER, DB_PASSWORD, etc.

# 5. Initialize database
export FLASK_APP=app.py
export FLASK_ENV=development
flask shell << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database initialized!')
EOF

python init_db.py

# 6. Run
flask run

# 7. Open http://localhost:5000
```

---

## 🚀 Option 3: Production Deployment (10 minutes)

**Best for:** Production environment on VPS or cloud server

```bash
# Step 1: Prepare deployment
chmod +x scripts/deploy_production.sh
cp .env.example .env.production

# Step 2: Edit production configuration
nano .env.production
# Update:
# - SECRET_KEY (generate new one)
# - DB_USER, DB_PASSWORD
# - DB_HOST (your server/RDS hostname)
# - DB_NAME

# Step 3: Deploy with one command
./scripts/deploy_production.sh

# This will:
# ✓ Verify Docker is installed
# ✓ Create database backup
# ✓ Build Docker images
# ✓ Start containers
# ✓ Initialize database
# ✓ Create performance indexes
# ✓ Run health checks

# Step 4: Access application
# → http://<your-server-ip>:5000
```

**Monitor deployment:**
```bash
docker-compose logs -f app
docker-compose logs -f postgres
```

---

## ☁️ Option 4: AWS RDS Deployment (20 minutes)

**Best for:** Enterprise production with managed database

```bash
# Step 1: Create RDS PostgreSQL instance in AWS Console
# Settings:
# - Engine: PostgreSQL 14+
# - Instance size: db.t3.micro (or larger)
# - Multi-AZ: Yes
# - Storage: 100GB
# - Backup retention: 30 days

# Step 2: Create database and user
# Download pgAdmin or use AWS RDS Query Editor
CREATE DATABASE dwaraka_mess;
CREATE USER dwaraka_user WITH PASSWORD 'your_secure_password';
GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;

# Step 3: Update .env.production
# DB_HOST=<rds-endpoint-from-aws>
# DB_USER=dwaraka_user
# DB_PASSWORD=your_secure_password
# DB_NAME=dwaraka_mess

# Step 4: Deploy application (same as Option 3)
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh
```

---

## 📋 Deployment Checklist

- [ ] Environment file created and configured
- [ ] PostgreSQL is accessible
- [ ] `requirements.txt` installed
- [ ] Database initialized (`db.create_all()`)
- [ ] Sample data seeded (`python init_db.py`)
- [ ] Application starts without errors
- [ ] Login works
- [ ] File uploads work
- [ ] Subscription features work

---

## 🧪 Verify Installation

```bash
# Check if PostgreSQL is running
# Docker: docker-compose ps
# Local: psql -U postgres

# Check if application starts
python -c "from app import app; print('✅ App loads')"

# Test database connection
python << 'EOF'
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.session.execute("SELECT 1")
    print("✅ Database connection OK")
EOF

# View sample data
docker-compose exec postgres psql -U postgres -d dwaraka_mess -c "SELECT COUNT(*) FROM users;"

# Run validation script
python validate_postgresql_setup.py
```

---

## 💾 Backup Setup (Recommended)

### Automated Daily Backups

```bash
# Make backup script executable
chmod +x scripts/backup_database.sh

# Test backup
./scripts/backup_database.sh full

# Schedule automatic backups (Linux/macOS)
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /path/to/D_mess/scripts/backup_database.sh full

# Test cron setup
./scripts/backup_database.sh list
```

### Manual Backup

```bash
# Full backup
./scripts/backup_database.sh full

# View backups
./scripts/backup_database.sh list

# Restore from backup
./scripts/backup_database.sh restore backups/full_backup_20260616_020000.sql.gz
```

---

## 🆘 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs postgres
docker-compose logs app

# Rebuild
docker-compose down -v
docker-compose up --build -d
```

### Connection refused

```bash
# Verify PostgreSQL is running
docker-compose ps

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Application crashes

```bash
# Check application logs
docker-compose logs app

# Check if database is ready
docker-compose exec postgres pg_isready -U postgres

# Try reinitializing
docker-compose exec app python init_db.py
```

### Slow performance

```bash
# Create performance indexes
docker-compose exec app flask shell << 'EOF'
from app import app, db
from sqlalchemy import text
with app.app_context():
    db.session.execute(text("ANALYZE;"))
    db.session.commit()
    print("Database analyzed")
EOF

# Increase connection pool in .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

## 📚 Full Documentation

- **Quick Setup:** This file (you are here)
- **Detailed Guide:** `SETUP_POSTGRES.md`
- **Technical Reference:** `POSTGRESQL_MIGRATION.md`
- **Migration Summary:** `POSTGRESQL_SHIFT_COMPLETE.md`
- **Docker Reference:** `docker-compose.yml`

---

## 🎉 Next Steps After Setup

1. **Test the application**
   - Login with provided credentials
   - Test subscription features
   - Test file uploads

2. **Configure backup**
   - Setup automated backups (see above)
   - Test restore procedure

3. **For production**
   - Generate new SECRET_KEY
   - Update connection pool settings
   - Setup monitoring/alerting
   - Document emergency procedures

4. **Ongoing maintenance**
   - Monitor backup logs
   - Review performance metrics
   - Update documentation

---

## 💡 Pro Tips

```bash
# Quick database backup before making changes
./scripts/backup_database.sh full

# Check application health
curl http://localhost:5000

# Monitor logs in real-time
docker-compose logs -f

# Access PostgreSQL directly for debugging
docker-compose exec postgres psql -U postgres -d dwaraka_mess

# Clean up and reset everything
docker-compose down -v
docker-compose up --build -d

# View database size
docker-compose exec postgres psql -U postgres -d dwaraka_mess -c \
  "SELECT pg_size_pretty(pg_database_size('dwaraka_mess'));"
```

---

## ❓ FAQ

**Q: Can I use this locally and production?**
A: Yes! Use Docker Compose locally, production deployment script for servers.

**Q: How do I backup my data?**
A: Run `./scripts/backup_database.sh full` for manual backups, or setup cron for automated.

**Q: How often should I backup?**
A: Daily is recommended. Use `0 2 * * * /path/to/backup_database.sh full` in crontab.

**Q: Can I migrate from SQLite later?**
A: Yes, but since we're starting fresh with PostgreSQL, this project is optimized for it.

**Q: What about SSL/TLS?**
A: Configure in `.env` if your database requires it: `DB_SSLMODE=require`

**Q: How do I scale to 10K users?**
A: Increase pool size, add indexes (already done), and consider read replicas.

---

✅ **Ready to deploy? Choose an option above and follow the steps!**
