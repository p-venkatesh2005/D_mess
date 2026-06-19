# PostgreSQL Database Connections - Dwaraka Mess System

## 🔗 Connection Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DWARAKA MESS APPLICATION                         │
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐ │
│  │   Flask     │───▶│  config.py   │───▶│  PostgreSQL Connection   │ │
│  │   App       │    │              │    │  String Builder          │ │
│  └─────────────┘    └──────────────┘    └──────────────────────────┘ │
│         │                                           │                  │
│         │                                           ▼                  │
│         │                              ┌────────────────────────────┐ │
│         │                              │  SQLAlchemy Engine         │ │
│         │                              │  with Connection Pool      │ │
│         │                              │                            │ │
│         │                              │  Pool Size: 10 (dev)       │ │
│         │                              │  Max Overflow: 20 (dev)    │ │
│         │                              │  Pool Recycle: 3600s       │ │
│         │                              │  Pool Pre-Ping: Enabled    │ │
│         │                              └────────────────────────────┘ │
│         │                                           │                  │
│         └───────────────────────────────────────────┘                  │
│                                                     │                  │
└─────────────────────────────────────────────────────┼──────────────────┘
                                                      │
                                                      ▼
                      ┌────────────────────────────────────────────────┐
                      │         POSTGRESQL DATABASE SERVER             │
                      │                                                │
                      │  Host: localhost (or cloud provider)           │
                      │  Port: 5432                                    │
                      │  Database: dwaraka_mess                        │
                      │  User: postgres                                │
                      │                                                │
                      │  ┌──────────────────────────────────────────┐ │
                      │  │          DATABASE TABLES                 │ │
                      │  │                                          │ │
                      │  │  • users           (authentication)      │ │
                      │  │  • students        (profiles)            │ │
                      │  │  • payments        (transactions)        │ │
                      │  │  • subscriptions   (monthly subs)        │ │
                      │  │  • orders          (meal orders)         │ │
                      │  │  • menus           (daily menus)         │ │
                      │  │  • attendance      (meal tracking)       │ │
                      │  │  • leave_requests  (absences)            │ │
                      │  │  • announcements   (notices)             │ │
                      │  │  • feedback        (ratings)             │ │
                      │  │  • qr_scans        (QR attendance)       │ │
                      │  │  • hostlers        (hostel residents)    │ │
                      │  │  • room_listings   (room ads)            │ │
                      │  │                                          │ │
                      │  └──────────────────────────────────────────┘ │
                      └────────────────────────────────────────────────┘
```

---

## 📊 Connection Flow

### 1. Application Startup

```python
# app.py
from config import config
app.config.from_object(config[config_name])
db.init_app(app)
```

### 2. Configuration Loading

```python
# config.py
SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}
```

### 3. Connection Pool Creation

SQLAlchemy creates a connection pool with:
- **Initial connections:** 10 (configurable via `DB_POOL_SIZE`)
- **Additional connections:** Up to 20 more when needed (`DB_MAX_OVERFLOW`)
- **Total max connections:** 30 concurrent connections
- **Connection recycling:** Every 3600 seconds (1 hour)
- **Pre-ping:** Tests connection before use to avoid stale connections

### 4. Query Execution

```python
# Any database operation
from extensions import db
result = db.session.execute("SELECT * FROM users")
```

The connection pool:
1. Checks if a connection is available
2. Tests connection with pre-ping
3. Executes query
4. Returns connection to pool

---

## 🔧 Connection Configuration

### Environment Variables

| Variable | Default | Production | Description |
|----------|---------|------------|-------------|
| `DB_USER` | `postgres` | Custom | Database username |
| `DB_PASSWORD` | `postgres` | Secure password | Database password |
| `DB_HOST` | `localhost` | RDS/Cloud endpoint | Database host |
| `DB_PORT` | `5432` | `5432` | PostgreSQL port |
| `DB_NAME` | `dwaraka_mess` | `dwaraka_mess_prod` | Database name |
| `DB_POOL_SIZE` | `10` (dev) | `20-50` | Base connection pool size |
| `DB_POOL_RECYCLE` | `3600` | `1800` | Seconds before recycling |
| `DB_MAX_OVERFLOW` | `20` | `40-100` | Extra connections allowed |

### Connection String Format

**Standard:**
```
postgresql://username:password@hostname:port/database_name
```

**Example (Development):**
```
postgresql://postgres:postgres@localhost:5432/dwaraka_mess
```

**Example (Production - AWS RDS):**
```
postgresql://admin:SecurePass123@dwaraka-db.xxxxx.rds.amazonaws.com:5432/dwaraka_mess_prod
```

**Cloud Platform (Railway, Heroku):**
```
Use DATABASE_URL environment variable directly
```

---

## 🏗️ Connection Pool Architecture

### Pool States

```
┌─────────────────────────────────────────────────────────────┐
│                    CONNECTION POOL                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AVAILABLE CONNECTIONS                   │  │
│  │  [Conn1] [Conn2] [Conn3] [Conn4] [Conn5] ... [Conn10] │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ checkout()                       │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              CHECKED OUT (In Use)                    │  │
│  │  [Conn6 → Query] [Conn7 → Query]                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ return()                         │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              OVERFLOW CONNECTIONS                    │  │
│  │  Created when pool is exhausted                      │  │
│  │  Max: 20 additional connections                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Connection Lifecycle

1. **Creation:** Pool creates initial connections on app startup
2. **Checkout:** App requests connection from pool
3. **Pre-ping:** Pool tests connection is alive before giving it out
4. **Use:** App executes queries using the connection
5. **Return:** Connection returned to pool after use
6. **Recycle:** Old connections recycled after `pool_recycle` seconds
7. **Overflow:** Extra connections created if pool exhausted
8. **Cleanup:** Overflow connections closed when no longer needed

---

## 🔄 Connection Usage in Application

### Blueprint Connections

Each blueprint uses the same shared connection pool:

```python
# blueprints/admin.py
from extensions import db

@admin_bp.route('/students')
def students():
    students = Student.query.all()  # Uses pool connection
    return render_template('admin/students.html', students=students)
```

### Transaction Management

```python
from extensions import db

# Automatic transaction
try:
    user = User(name='John', phone='1234567890')
    db.session.add(user)
    db.session.commit()  # Connection returned to pool after commit
except:
    db.session.rollback()  # Connection returned to pool after rollback
```

### Multiple Models

All models share the same connection pool:

```python
# Single transaction, single connection
user = User(name='John')
db.session.add(user)
db.session.flush()

student = Student(user_id=user.id)
db.session.add(student)
db.session.commit()  # One connection for entire transaction
```

---

## 📈 Connection Scaling

### Development (1-10 users)
```
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
Total: 15 max connections
```

### Small Production (10-100 users)
```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
Total: 30 max connections
```

### Medium Production (100-1000 users)
```
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
Total: 60 max connections
```

### Large Production (1000-10000 users)
```
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
Total: 150 max connections
```

### Enterprise (10000+ users)
```
DB_POOL_SIZE=100
DB_MAX_OVERFLOW=200
Total: 300 max connections
+ Read replicas for reporting
+ Connection pooler (PgBouncer)
```

---

## 🔍 Monitoring Connections

### Check Active Connections (PostgreSQL)

```sql
-- Total connections
SELECT count(*) FROM pg_stat_activity;

-- Connections per database
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;

-- Active queries
SELECT pid, usename, application_name, client_addr, state, query
FROM pg_stat_activity
WHERE state = 'active';

-- Connection pool status
SELECT count(*) as total,
       count(*) FILTER (WHERE state = 'active') as active,
       count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = 'dwaraka_mess';
```

### Application-Level Monitoring

```python
from extensions import db

# Get pool stats
engine = db.engine
pool = engine.pool

print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
print(f"Checked in: {pool.checkedin()}")
```

---

## 🚨 Connection Issues & Solutions

### Issue: Pool Overflow Error

**Symptom:** `QueuePool limit of size 10 overflow 20 reached`

**Solution:**
```bash
# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60
```

### Issue: Connection Lost

**Symptom:** `server closed the connection unexpectedly`

**Solution:** Pool pre-ping is already enabled - handles this automatically

### Issue: Slow Queries

**Symptom:** Connections held too long

**Solution:**
```python
# Enable query logging
SQLALCHEMY_ENGINE_OPTIONS = {
    'echo': True,  # Logs all queries
}

# Or use explain
from sqlalchemy import text
result = db.session.execute(text("EXPLAIN ANALYZE SELECT * FROM users"))
```

### Issue: Too Many Connections

**Symptom:** PostgreSQL max_connections exceeded

**Solution:**
```sql
-- Check PostgreSQL max connections
SHOW max_connections;

-- Increase max connections (requires restart)
ALTER SYSTEM SET max_connections = 200;

-- Restart PostgreSQL
-- sudo systemctl restart postgresql
```

---

## 🔒 Connection Security

### SSL/TLS Connections

For production, enable SSL:

```python
# .env
DB_SSLMODE=require

# Or in connection string
postgresql://user:pass@host:5432/db?sslmode=require
```

### Connection Timeouts

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_timeout': 30,  # Wait 30 seconds for connection
    'pool_recycle': 1800,
    'pool_pre_ping': True,
}
```

---

## ✅ Connection Health Checks

### Docker Health Check

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d dwaraka_mess"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Application Health Check

```python
@app.route('/health/db')
def db_health():
    try:
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'postgres'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

---

## 📊 Connection Summary

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **Driver** | `psycopg2-binary` | PostgreSQL adapter |
| **ORM** | `SQLAlchemy 2.0` | Database abstraction |
| **Pool Size** | 10 (dev) / 20 (prod) | Base connections |
| **Overflow** | 20 (dev) / 40 (prod) | Extra connections |
| **Recycle** | 3600s (dev) / 1800s (prod) | Connection lifetime |
| **Pre-ping** | Enabled | Stale connection detection |
| **Protocol** | `postgresql://` | Connection protocol |
| **Port** | 5432 | PostgreSQL default |

---

## 🚀 Testing Connections

### Quick Test

```bash
python check_db_connections.py
```

### Comprehensive Test

```bash
python test_postgresql_connection.py
```

### Manual psql Test

```bash
# Local
psql -h localhost -U postgres -d dwaraka_mess

# Remote
psql -h your-host.com -U dwaraka_user -d dwaraka_mess_prod
```

---

## 📚 Related Documentation

- **[SETUP_POSTGRES.md](SETUP_POSTGRES.md)** - Setup instructions
- **[POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md)** - Complete technical guide
- **[docker-compose.yml](docker-compose.yml)** - Docker configuration
- **[config.py](config.py)** - Connection configuration code

---

**Status:** ✅ All connections configured and tested  
**Last Updated:** 2026-06-16  
**PostgreSQL Version:** 14+
