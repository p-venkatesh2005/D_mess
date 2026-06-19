#!/bin/bash
# Production Deployment Script for Dwaraka Mess Management System
# Usage: ./scripts/deploy_production.sh

set -e

echo "🚀 Dwaraka Mess - Production Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ .env.production not found!${NC}"
    echo "Please create .env.production before deploying"
    exit 1
fi

# Load production environment
export $(cat .env.production | grep -v '^#' | xargs)

echo -e "${YELLOW}📋 Pre-deployment checks:${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check PostgreSQL connection (optional)
echo -e "${YELLOW}🔍 Verifying PostgreSQL connection...${NC}"
if command -v pg_isready &> /dev/null; then
    if pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is reachable${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL not reachable (may be acceptable if using AWS RDS)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  pg_isready not available, skipping PostgreSQL check${NC}"
fi

# Backup existing database (if container exists)
echo -e "${YELLOW}💾 Creating backup...${NC}"
BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

if docker ps -a | grep -q dwaraka_mess_db; then
    echo "Creating PostgreSQL backup..."
    docker exec dwaraka_mess_db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/dwaraka_mess_$BACKUP_TIMESTAMP.sql.gz
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR/dwaraka_mess_$BACKUP_TIMESTAMP.sql.gz${NC}"
else
    echo -e "${YELLOW}⚠️  No existing database container found, skipping backup${NC}"
fi

# Stop existing containers (if running)
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down || true

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.yml build

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f docker-compose.yml up -d

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to start...${NC}"
for i in {1..30}; do
    if docker exec dwaraka_mess_db pg_isready -U $DB_USER -d $DB_NAME > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Initialize database if needed
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
docker exec -it dwaraka_mess_app python init_db.py || {
    echo -e "${YELLOW}⚠️  Database initialization script may need manual review${NC}"
}

# Run migrations (if using Alembic in future)
# docker exec dwaraka_mess_app flask db upgrade

# Apply performance indexes
echo -e "${YELLOW}📊 Applying performance indexes...${NC}"
docker exec dwaraka_mess_app flask shell << EOF
from app import app, db
from sqlalchemy import text
with app.app_context():
    try:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_students_status ON students(subscription_status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
            "CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_qr_scans_date ON qr_scans(scan_date)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_year_month ON subscriptions(year, month)",
        ]
        for idx in indexes:
            db.session.execute(text(idx))
        db.session.commit()
        print("Indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
EOF

# Health check
echo -e "${YELLOW}🏥 Running health checks...${NC}"
sleep 5

if docker ps | grep -q dwaraka_mess_app; then
    echo -e "${GREEN}✓ Application container is running${NC}"
else
    echo -e "${RED}❌ Application container failed to start${NC}"
    docker-compose logs app
    exit 1
fi

if docker ps | grep -q dwaraka_mess_db; then
    echo -e "${GREEN}✓ Database container is running${NC}"
else
    echo -e "${RED}❌ Database container failed to start${NC}"
    docker-compose logs postgres
    exit 1
fi

# Test application endpoint
echo -e "${YELLOW}🌐 Testing application endpoint...${NC}"
if curl -s http://localhost:5000 > /dev/null; then
    echo -e "${GREEN}✓ Application is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Application endpoint not responding yet (may need more time)${NC}"
fi

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📊 Container Status:"
docker-compose ps
echo ""
echo "📝 Next Steps:"
echo "  1. Monitor logs: docker-compose logs -f app"
echo "  2. Access application: http://localhost:5000"
echo "  3. View database: docker exec -it dwaraka_mess_db psql -U $DB_USER -d $DB_NAME"
echo "  4. Backup location: $BACKUP_DIR/"
echo ""
echo "🔧 Useful Commands:"
echo "  - Restart: docker-compose restart"
echo "  - Stop: docker-compose down"
echo "  - Logs: docker-compose logs -f [service_name]"
echo "  - Rebuild: docker-compose up -d --build"
echo ""
