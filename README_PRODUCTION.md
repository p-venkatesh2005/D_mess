# 🍽️ Dwaraka Mess Management System

## Production-Ready PostgreSQL Deployment

A complete mess management system built with Flask and PostgreSQL, featuring subscription management, QR-based attendance, meal ordering, payment tracking, and comprehensive admin controls.

---

## ✨ Features

### 👨‍💼 Admin Features
- Real-time dashboard with statistics and charts
- Student management (add, edit, deactivate)
- Subscription management and payment verification
- Menu planning and daily meal management
- Attendance tracking and reporting
- Leave request approval
- Announcement posting
- Feedback and complaint management
- Room listing management for students
- Excel export for attendance reports

### 👨‍🎓 Student Features
- Personal dashboard with subscription status
- Monthly subscription with automated renewal
- Payment screenshot upload with deduplication
- QR code-based meal attendance
- Daily menu viewing
- Meal ordering (breakfast, lunch, dinner, tiffin)
- Leave request submission (5-10 days)
- Feedback and ratings
- Announcement viewing
- Room listings search

### 🏠 Hostler Features
- Separate dashboard for hostel residents
- Complaint submission
- Food quality feedback
- Room availability browsing

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd dwaraka-mess

# 2. Create environment file
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker exec -it dwaraka_mess_app python init_db.py

# 5. Access application
# http://localhost:5000
```

### Option 2: Manual Setup

```bash
# 1. Install PostgreSQL 14+
# 2. Create database
createdb dwaraka_mess

# 3. Setup Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Initialize database
python init_db.py

# 6. Run application
python app.py
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# PostgreSQL Configuration
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dwaraka_mess

# Connection Pool Settings
DB_POOL_SIZE=20
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=40

# Application Settings
UPLOAD_FOLDER=static/uploads/payments
MAX_CONTENT_LENGTH=5242880
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📊 Database Schema

### 13 Tables
- **users** - Authentication and user management
- **students** - Student profiles and subscription status
- **payments** - Payment tracking with screenshot deduplication
- **subscriptions** - Monthly subscription records
- **orders** - Meal orders (breakfast, lunch, dinner, tiffin)
- **menus** - Daily menu planning
- **attendance** - Student attendance records
- **leave_requests** - Leave applications
- **announcements** - Notice board
- **feedback** - Ratings and complaints
- **qr_scans** - QR-based meal attendance
- **hostlers** - Hostel resident profiles
- **room_listings** - Room advertisements

---

## 🔐 Default Credentials

**Admin:**
- Phone: `9999999999`
- Password: `admin123`

**Student (Sample):**
- Phone: `8111111111`
- Password: `student123`

⚠️ **IMPORTANT:** Change these in production!

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment Script

```bash
chmod +x scripts/deploy_production.sh
./scripts/deploy_production.sh
```

This script will:
- Verify Docker installation
- Create database backup
- Build and start containers
- Initialize database
- Create performance indexes
- Run health checks

---

## 💾 Backup & Recovery

### Automated Backups

```bash
# Setup daily backups at 2 AM
chmod +x scripts/backup_database.sh
crontab -e
# Add: 0 2 * * * /path/to/scripts/backup_database.sh full
```

### Manual Backup

```bash
# Create backup
./scripts/backup_database.sh full

# List backups
./scripts/backup_database.sh list

# Restore backup
./scripts/backup_database.sh restore backups/full_backup_*.sql.gz
```

---

## 📈 Performance Optimization

### For 10K+ Users

Update `.env`:
```bash
DB_POOL_SIZE=50
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=100
```

PostgreSQL configuration:
```sql
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### Pre-created Indexes

The deployment script automatically creates these indexes:
- `idx_students_status` - Fast subscription status queries
- `idx_payments_status` - Payment filtering
- `idx_orders_date` - Date-based order queries
- `idx_attendance_date` - Attendance reports
- `idx_qr_scans_date` - QR scan analysis
- `idx_subscriptions_year_month` - Monthly reports

---

## 🔒 Security Features

- ✅ CSRF protection enabled
- ✅ Session cookie security (HttpOnly, SameSite)
- ✅ Password hashing with scrypt
- ✅ File upload validation
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Screenshot deduplication (SHA-256 hashing)
- ✅ Connection pool pre-ping (prevents stale connections)
- ✅ Environment variable-based configuration
- ✅ Production-ready error handling

---

## 🧪 Testing

### Health Check

```bash
# Application health
curl http://localhost:5000/

# Database connection
docker exec -it dwaraka_mess_app python -c "from app import app, db; from sqlalchemy import text; app.app_context().push(); db.session.execute(text('SELECT 1')); print('✅ Database OK')"
```

### Run Validation

```bash
python validate_postgresql_setup.py
```

---

## 📚 Documentation

- **POSTGRESQL_README.md** - Complete PostgreSQL guide
- **QUICK_START_POSTGRESQL.md** - Quick deployment guide
- **POSTGRESQL_MIGRATION.md** - Technical migration details
- **DATABASE_CONNECTIONS.md** - Connection architecture
- **POSTGRESQL_COMPATIBILITY_FIXES.md** - SQLite→PostgreSQL fixes
- **DOCKER_SETUP_WINDOWS.md** - Windows Docker setup
- **START_WITH_DOCKER.txt** - Docker installation guide

---

## 🌍 Cloud Deployment

### AWS RDS

```bash
# 1. Create RDS PostgreSQL instance
# 2. Update .env.production
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=your-secure-password
DB_NAME=dwaraka_mess_prod

# 3. Deploy application
./scripts/deploy_production.sh
```

### Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Initialize project
railway init

# 3. Add PostgreSQL
railway add -d postgresql

# 4. Deploy
git push railway main
```

### Heroku

```bash
# 1. Create app
heroku create dwaraka-mess

# 2. Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# 3. Deploy
git push heroku main

# 4. Initialize database
heroku run python init_db.py
```

---

## 🛠️ Tech Stack

- **Backend:** Flask 3.0.3
- **Database:** PostgreSQL 16 with connection pooling
- **ORM:** SQLAlchemy 2.0.23
- **Auth:** Flask-Login with role-based access control
- **Forms:** Flask-WTF with CSRF protection
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **Deployment:** Docker, Docker Compose
- **Python:** 3.11+

---

## 📋 Production Checklist

- [ ] Generate strong SECRET_KEY
- [ ] Update admin credentials
- [ ] Configure .env.production
- [ ] Enable SSL/TLS for database
- [ ] Setup automated backups
- [ ] Configure monitoring/alerting
- [ ] Test backup restore procedure
- [ ] Setup log rotation
- [ ] Configure firewall rules
- [ ] Enable connection pooling
- [ ] Create read replicas (if needed)
- [ ] Document emergency procedures

---

## 🆘 Troubleshooting

### Common Issues

**PostgreSQL connection refused:**
```bash
# Check if PostgreSQL is running
docker-compose ps
# Restart database
docker-compose restart postgres
```

**Pool overflow error:**
```bash
# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60
```

**Application won't start:**
```bash
# Check logs
docker-compose logs app
# Rebuild
docker-compose down && docker-compose up -d --build
```

---

## 📞 Support

For issues and questions:
1. Check documentation in `/docs` folder
2. Review logs: `docker-compose logs`
3. Run validation: `python validate_postgresql_setup.py`
4. Check health: `curl http://localhost:5000/`

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

Built with Flask, PostgreSQL, and Docker for production-grade deployment.

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-06-19  
**PostgreSQL:** 16+  
**Python:** 3.11+  
**Docker:** 24+
