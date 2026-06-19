# PostgreSQL Migration Guide - Dwaraka Mess Management System

## Overview
This document provides a complete guide for running the Dwaraka Mess Management System with PostgreSQL. The system has been configured for production-grade deployment with connection pooling, health checks, and best practices.

---

## 1. Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (optional, recommended)

### Option A: Using Docker Compose (Recommended)

```bash
# 1. Create .env file from example
cp .env.example .env

# 2. Build and start services
docker-compose up -d

# 3. Initialize database and create tables
docker exec -it dwaraka_mess_app flask shell
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     print("Database initialized!")
>>> exit()

# 4. Seed initial data (admin user, etc.)
docker exec -it dwaraka_mess_app python init_db.py

# 5. Access application
# Open browser: http://localhost:5000
```

### Option B: Manual PostgreSQL Setup

```bash
# 1. Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# 2. Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Create database and user
sudo -u postgres psql
postgres=# CREATE DATABASE dwaraka_mess;
postgres=# CREATE USER dwaraka_user WITH PASSWORD 'your_secure_password';
postgres=# ALTER ROLE dwaraka_user SET client_encoding TO 'utf8';
postgres=# ALTER ROLE dwaraka_user SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE dwaraka_user SET default_transaction_deferrable TO on;
postgres=# ALTER ROLE dwaraka_user SET default_transaction_level TO 'read committed';
postgres=# GRANT ALL PRIVILEGES ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=# \q

# 4. Create .env file
cp .env.example .env

# 5. Update .env with your PostgreSQL credentials
# DB_USER=dwaraka_user
# DB_PASSWORD=your_secure_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=dwaraka_mess

# 6. Install Python dependencies
pip install -r requirements.txt

# 7. Initialize Flask app and create tables
export FLASK_ENV=development
export FLASK_APP=app.py
flask shell
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     print("Database initialized!")
>>> exit()

# 8. Seed initial data
python init_db.py

# 9. Run the application
flask run
```

---

## 2. Database Configuration

### Connection String Format

```
postgresql://username:password@hostname:port/database_name
```

### Configuration in config.py

The application uses the following environment variables:

- `DB_USER` - PostgreSQL username (default: postgres)
- `DB_PASSWORD` - PostgreSQL password (default: postgres)
- `DB_HOST` - PostgreSQL host (default: localhost)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (default: dwaraka_mess)

**OR** use `DATABASE_URL` directly for cloud deployments.

### Connection Pooling Configuration

The application uses SQLAlchemy connection pooling with these settings:

- `pool_size=10` (dev) / `pool_size=20` (prod) - Base connection pool size
- `max_overflow=20` (dev) / `max_overflow=40` (prod) - Additional connections allowed
- `pool_recycle=3600` (dev) / `pool_recycle=1800` (prod) - Recycle connections after inactivity
- `pool_pre_ping=True` - Test connections before use (prevents "connection lost" errors)

**Recommendation for 10K+ users:**
```python
DB_POOL_SIZE=30
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=60
```

---

## 3. Database Schema

### Tables and Relationships

```
users (15 columns)
├── student (1-to-1)
│   ├── subscriptions (1-to-many)
│   ├── payments (1-to-many)
│   ├── attendances (1-to-many)
│   ├── leave_requests (1-to-many)
│   └── qr_scans (1-to-many)
├── orders (1-to-many)
├── feedbacks (1-to-many)
└── hostler (1-to-1)

Independent tables:
├── menus
├── announcements
└── room_listings
```

### Indexes Automatically Created

SQLAlchemy creates indexes for:
- Primary keys
- Foreign keys
- Unique constraints

**Recommended additional indexes for performance:**

```sql
-- For faster queries on common filters
CREATE INDEX idx_students_status ON students(subscription_status);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_leave_requests_status ON leave_requests(status);
CREATE INDEX idx_qr_scans_date ON qr_scans(scan_date);

-- For monthly/yearly reports
CREATE INDEX idx_subscriptions_year_month ON subscriptions(year, month);
```

Apply these indexes:
```bash
# Via Flask shell
flask shell
>>> from app import app, db
>>> with app.app_context():
...     db.session.execute("""CREATE INDEX IF NOT EXISTS idx_students_status ON students(subscription_status)""")
...     db.session.execute("""CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)""")
...     # ... (add more indexes)
...     db.session.commit()
```

---

## 4. Deployment Options

### Option 1: AWS RDS PostgreSQL

```bash
# 1. Create RDS instance in AWS console
# - Engine: PostgreSQL 14+
# - Multi-AZ: Yes (for high availability)
# - Automated backups: 30 days
# - Enhanced monitoring: Enabled

# 2. Create database and user
aws rds-describe-db-instances --db-instance-identifier dwaraka-mess-db
# Get endpoint and port

# 3. Connect and setup
psql -h <rds-endpoint> -U admin -d postgres
postgres=> CREATE DATABASE dwaraka_mess;
postgres=> CREATE USER dwaraka_user WITH PASSWORD 'secure_password';
postgres=> GRANT ALL ON DATABASE dwaraka_mess TO dwaraka_user;
postgres=> \q

# 4. Update .env.production
# DB_HOST=<rds-endpoint>
# DB_USER=dwaraka_user
# DB_PASSWORD=secure_password
# DB_NAME=dwaraka_mess

# 5. Deploy application with updated .env
```

### Option 2: Railway (PaaS - Easiest)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Create project
railway init

# 3. Add PostgreSQL
railway add -d postgresql

# 4. Link variables from Railway to Flask app
# Set DATABASE_URL from Railway PostgreSQL environment

# 5. Deploy
git push
```

### Option 3: Docker on VPS

```bash
# 1. SSH into VPS
ssh user@your-vps-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Clone repository
git clone <repository-url>
cd D_mess

# 4. Create .env.production
cp .env.example .env.production
# Update with production values

# 5. Build and run
docker-compose -f docker-compose.yml up -d

# 6. Initialize database
docker exec -it dwaraka_mess_app flask shell
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### Option 4: Google Cloud SQL

```bash
# Similar to AWS RDS - use Cloud SQL Admin API
gcloud sql instances create dwaraka-mess \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Get connection details and configure .env
```

---

## 5. Backup and Recovery

### Automated Backups

#### Option 1: pg_dump Script

```bash
#!/bin/bash
# File: backup_db.sh

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups/dwaraka_mess"
DB_NAME="dwaraka_mess"

mkdir -p $BACKUP_DIR

# Full backup
pg_dump -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} | gzip > $BACKUP_DIR/dwaraka_mess_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/dwaraka_mess_$TIMESTAMP.sql.gz"
```

#### Option 2: Cron Job

```bash
# Add to crontab for daily backups
0 2 * * * /path/to/backup_db.sh >> /var/log/backup.log 2>&1
```

### Recovery

```bash
# Restore from backup
gunzip < /backups/dwaraka_mess/dwaraka_mess_20260616_020000.sql.gz | \
  psql -h localhost -U dwaraka_user -d dwaraka_mess
```

---

## 6. Monitoring and Health Checks

### Health Check Endpoint

```bash
# Docker health check runs every 30 seconds
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=2)"
```

### Database Connection Monitoring

```python
# Add to Flask app for monitoring
from sqlalchemy import text

@app.route('/health/db')
def db_health():
    try:
        result = db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'postgres'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

### Query Performance Logging

Enable in development:

```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    # ...
    'echo': True,  # Log all SQL queries
}
```

---

## 7. Production Deployment Checklist

- [ ] Generate strong SECRET_KEY
- [ ] Set `FLASK_ENV=production`
- [ ] Enable `SESSION_COOKIE_SECURE=True`
- [ ] Configure PostgreSQL with backup retention
- [ ] Set up monitoring (CPU, memory, connections)
- [ ] Configure log rotation
- [ ] Enable SSL/TLS for database connections
- [ ] Test backup and recovery procedures
- [ ] Set up alerting for connection pool exhaustion
- [ ] Document emergency procedures
- [ ] Enable WAL (Write-Ahead Logging) on PostgreSQL
- [ ] Configure replication for HA (if needed)
- [ ] Tune `shared_buffers` and `work_mem` based on server specs
- [ ] Create read replicas if needed (for reporting)

---

## 8. Troubleshooting

### Connection Pool Exhaustion

**Symptom:** `QueuePool limit of size 20 overflow 40 reached`

**Solution:**
```python
# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60

# OR close connections properly in code
db.session.close()
```

### "Connection Lost" Errors

**Symptom:** `SSL SYSCALL error: No connection could be made`

**Solution:** `pool_pre_ping=True` is already enabled in config.py

### Slow Queries

**Solution:** Add indexes and analyze

```sql
-- Analyze slow query
EXPLAIN ANALYZE SELECT * FROM orders WHERE order_date = '2026-06-16';

-- Create index if needed
CREATE INDEX idx_orders_date ON orders(order_date);
```

### Database Not Starting in Docker

```bash
# Check logs
docker-compose logs postgres

# Restart and rebuild
docker-compose down -v
docker-compose up --build -d
```

---

## 9. Performance Tuning for 10K+ Users

### PostgreSQL Configuration

```sql
-- Connect to postgres as admin
psql -U postgres

-- Increase connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET random_page_cost = 1.1;

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

### Application Configuration

```bash
# .env for high load
DB_POOL_SIZE=40
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=80
```

### Query Optimization

```python
# Use select_related for foreign keys
students = Student.query.select_related('user').all()

# Use lazy loading where appropriate
orders = Order.query.options(db.joinedload('user')).all()
```

---

## 10. Migration from SQLite (If Needed)

This project starts fresh with PostgreSQL, but if you have existing SQLite data:

```bash
# 1. Export from SQLite
sqlite3 dwaraka_mess.db .dump > dump.sql

# 2. Convert to PostgreSQL syntax
# (Many differences exist - manual review needed)

# 3. Import to PostgreSQL
psql -h localhost -U dwaraka_user -d dwaraka_mess < dump.sql
```

**Note:** SQLite and PostgreSQL have syntax differences. Manual verification is required.

---

## 11. Support and Further Information

- PostgreSQL Docs: https://www.postgresql.org/docs/
- Flask-SQLAlchemy Docs: https://flask-sqlalchemy.palletsprojects.com/
- SQLAlchemy Connection Pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
- Docker Docs: https://docs.docker.com/

---

**Version:** 1.0  
**Last Updated:** 2026-06-16  
**Status:** Ready for Production
