# PostgreSQL Setup Guide - Dwaraka Mess Management System

Quick reference for setting up and running the application with PostgreSQL.

## 🚀 Quick Start (5 minutes)

### With Docker Compose (Recommended)

```bash
# 1. Clone and setup
git clone <repository-url>
cd D_mess
cp .env.example .env

# 2. Start everything (PostgreSQL + App)
docker-compose up -d

# 3. Initialize database
docker exec -it dwaraka_mess_app bash -c "
  flask shell << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database initialized!')
EOF
  python init_db.py
"

# 4. Open browser
# http://localhost:5000
```

### Without Docker

```bash
# 1. Install PostgreSQL 14+
# Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib
# macOS: brew install postgresql@14
# Windows: Download from https://www.postgresql.org/download/windows/

# 2. Start PostgreSQL
# Ubuntu/Debian: sudo systemctl start postgresql
# macOS: brew services start postgresql@14
# Windows: Use PostgreSQL service from Start Menu

# 3. Create database
psql -U postgres
postgres=# CREATE DATABASE dwaraka_mess;
postgres=# CREATE USER dwaraka_user WITH PASSWORD 'secure_password_here';
postgres=# GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=# \q

# 4. Setup project
pip install -r requirements.txt
cp .env.example .env

# 5. Update .env
# DB_USER=dwaraka_user
# DB_PASSWORD=secure_password_here
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=dwaraka_mess

# 6. Initialize
export FLASK_APP=app.py
flask shell << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database initialized!')
EOF

python init_db.py

# 7. Run app
flask run
```

---

## 📁 File Structure

```
.
├── .env.example              # Environment template
├── .env.production           # Production config (create before deploy)
├── config.py                 # Database config with connection pooling
├── models.py                 # SQLAlchemy models (PostgreSQL compatible)
├── app.py                    # Flask app
├── init_db.py                # Database initialization and seeding
├── requirements.txt          # Python dependencies (includes psycopg2)
├── docker-compose.yml        # PostgreSQL + App setup
├── Dockerfile                # Application container
├── POSTGRESQL_MIGRATION.md   # Detailed migration guide
├── SETUP_POSTGRES.md         # This file
├── scripts/
│   ├── deploy_production.sh  # One-command production deployment
│   └── backup_database.sh    # Database backup/restore utility
└── blueprints/               # Flask blueprints
    ├── auth.py
    ├── admin.py
    ├── student.py
    └── hostler.py
```

---

## 🔧 Environment Variables

### Development (.env)

```bash
FLASK_ENV=development
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dwaraka_mess
DB_POOL_SIZE=10
```

### Production (.env.production)

```bash
FLASK_ENV=production
SECRET_KEY=<generate-strong-key>
DB_USER=<secure-username>
DB_PASSWORD=<secure-password>
DB_HOST=<production-host>
DB_PORT=5432
DB_NAME=dwaraka_mess_prod
DB_POOL_SIZE=20
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=40
```

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🐳 Docker Compose Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f postgres

# Access application shell
docker-compose exec app flask shell

# Access PostgreSQL directly
docker-compose exec postgres psql -U postgres -d dwaraka_mess

# Stop services
docker-compose down

# Restart
docker-compose restart

# Rebuild images
docker-compose up --build -d

# View status
docker-compose ps
```

---

## 📊 Database Operations

### Initialize Database

```bash
# Create tables
docker-compose exec app flask shell << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print('Tables created!')
EOF

# Seed sample data
docker-compose exec app python init_db.py
```

### Create Indexes

```bash
docker-compose exec app flask shell << 'EOF'
from app import app, db
from sqlalchemy import text

with app.app_context():
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_students_status ON students(subscription_status)",
        "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
    ]
    for idx in indexes:
        db.session.execute(text(idx))
    db.session.commit()
    print('Indexes created!')
EOF
```

### View Database Stats

```bash
docker-compose exec postgres psql -U postgres -d dwaraka_mess << 'EOF'
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
EOF
```

---

## 💾 Backup & Recovery

### Backup Database

```bash
# Using backup script
chmod +x scripts/backup_database.sh
./scripts/backup_database.sh full

# Manual backup
docker-compose exec postgres pg_dump -U postgres dwaraka_mess | gzip > backup.sql.gz

# List backups
ls -lh backups/
```

### Restore Database

```bash
# Using script
./scripts/backup_database.sh restore backups/full_backup_20260616_020000.sql.gz

# Manual restore
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U postgres -d dwaraka_mess
```

### Setup Automated Backups

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * /path/to/scripts/backup_database.sh full

# Test cron
crontab -l
```

---

## 🚀 Production Deployment

### One-Command Deployment

```bash
# Make scripts executable
chmod +x scripts/deploy_production.sh
chmod +x scripts/backup_database.sh

# Deploy
./scripts/deploy_production.sh
```

This script will:
- Verify prerequisites (Docker, Docker Compose)
- Create database backup
- Build Docker images
- Start containers
- Initialize database
- Apply performance indexes
- Run health checks

### AWS RDS PostgreSQL

```bash
# 1. Create RDS instance in AWS console
# 2. Create database and user
# 3. Update .env.production
# 4. Deploy

docker-compose -f docker-compose.yml up -d
```

---

## 🔍 Troubleshooting

### "Connection refused"

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### "UNIQUE constraint failed"

This has been fixed - email field is now optional and checked for duplicates programmatically.

### "Pool overflow"

Increase pool settings in .env:
```bash
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60
```

### "Slow queries"

Create indexes:
```bash
./scripts/deploy_production.sh  # Includes index creation
```

Or manually in application:
```bash
docker-compose exec app flask shell << 'EOF'
from app import app, db
from sqlalchemy import text
with app.app_context():
    db.session.execute(text("ANALYZE;"))
    db.session.commit()
EOF
```

---

## 📋 Deployment Checklist

- [ ] PostgreSQL 14+ installed and running
- [ ] `.env` file configured with database credentials
- [ ] `requirements.txt` installed (`pip install -r requirements.txt`)
- [ ] Database created (`CREATE DATABASE dwaraka_mess;`)
- [ ] Tables initialized (`db.create_all()`)
- [ ] Sample data seeded (`python init_db.py`)
- [ ] Application starts without errors (`flask run`)
- [ ] Login works with admin/student credentials
- [ ] Subscription features work
- [ ] File uploads work
- [ ] Backup script tested
- [ ] Production `.env.production` created with strong SECRET_KEY
- [ ] Connection pooling configured for your expected load
- [ ] Health checks configured
- [ ] Monitoring setup (optional but recommended)

---

## 🆘 Getting Help

### Useful Logs

```bash
# Application logs
docker-compose logs app

# Database logs
docker-compose logs postgres

# Full logs with timestamp
docker-compose logs --timestamps postgres

# Follow logs in real-time
docker-compose logs -f
```

### Database Connection Test

```bash
# From host machine
psql -h localhost -U dwaraka_user -d dwaraka_mess

# From inside application container
docker-compose exec app python << 'EOF'
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.session.execute("SELECT 1")
    print("✅ Database connection successful!")
EOF
```

### Query Logs (Debug Mode)

```python
# In config.py, set:
SQLALCHEMY_ENGINE_OPTIONS = {
    'echo': True,  # Logs all SQL queries
}
```

---

## 📖 Further Reading

- [POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md) - Comprehensive guide
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-06-16  
**PostgreSQL Version:** 14+  
**Python Version:** 3.11+
