#!/bin/bash
# PostgreSQL Backup Script for Dwaraka Mess Management System
# Usage: ./scripts/backup_database.sh [--full|--incremental]
# For automated backups, add to crontab: 0 2 * * * /path/to/backup_database.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_PATH:-./backups}"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FULL_BACKUP="$BACKUP_DIR/full_backup_$TIMESTAMP.sql.gz"
INCREMENTAL_DIR="$BACKUP_DIR/incremental"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
elif [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Create backup directory
mkdir -p $BACKUP_DIR
mkdir -p $INCREMENTAL_DIR

echo -e "${YELLOW}🔄 PostgreSQL Backup Script${NC}"
echo "===================================="
echo "Timestamp: $TIMESTAMP"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST"
echo "Backup Directory: $BACKUP_DIR"
echo ""

# Function to perform full backup
perform_full_backup() {
    echo -e "${YELLOW}📦 Performing full backup...${NC}"
    
    if command -v docker &> /dev/null && docker ps | grep -q dwaraka_mess_db; then
        # Docker container backup
        echo "Backing up from Docker container..."
        docker exec dwaraka_mess_db pg_dump \
            -U $DB_USER \
            -d $DB_NAME \
            -F custom \
            -b \
            -v \
            -f /tmp/backup.dump
        
        docker cp dwaraka_mess_db:/tmp/backup.dump - | gzip > $FULL_BACKUP
        docker exec dwaraka_mess_db rm /tmp/backup.dump
    else
        # Direct PostgreSQL backup
        echo "Backing up from direct PostgreSQL connection..."
        pg_dump \
            -h $DB_HOST \
            -U $DB_USER \
            -d $DB_NAME \
            -F custom \
            -b \
            -v | gzip > $FULL_BACKUP
    fi
    
    if [ -f "$FULL_BACKUP" ]; then
        SIZE=$(du -h "$FULL_BACKUP" | cut -f1)
        echo -e "${GREEN}✓ Full backup completed: $SIZE${NC}"
        echo "Location: $FULL_BACKUP"
    else
        echo -e "${RED}❌ Backup failed!${NC}"
        exit 1
    fi
}

# Function to perform incremental backup
perform_incremental_backup() {
    echo -e "${YELLOW}⚡ Performing incremental backup...${NC}"
    
    if ! [ -f "$FULL_BACKUP" ]; then
        # If no full backup today, use most recent one
        LATEST_FULL=$(ls -t $BACKUP_DIR/full_backup_*.sql.gz 2>/dev/null | head -1)
        if [ -z "$LATEST_FULL" ]; then
            echo -e "${YELLOW}⚠️  No full backup found, performing full backup instead${NC}"
            perform_full_backup
            return
        fi
    fi
    
    INCREMENTAL_BACKUP="$INCREMENTAL_DIR/incremental_$TIMESTAMP.sql.gz"
    
    # This is a simplified incremental using WAL archives
    # For production, consider using pg_basebackup with streaming replication
    echo "Note: True incremental backups require WAL archiving configuration"
    
    echo -e "${YELLOW}Using full backup + WAL stream approach${NC}"
    perform_full_backup
}

# Function to verify backup integrity
verify_backup() {
    echo -e "${YELLOW}🔍 Verifying backup integrity...${NC}"
    
    local backup_file=$1
    
    if ! command -v gunzip &> /dev/null; then
        echo -e "${YELLOW}⚠️  gunzip not available, skipping verification${NC}"
        return
    fi
    
    if gunzip -t "$backup_file" 2>/dev/null; then
        echo -e "${GREEN}✓ Backup file integrity verified${NC}"
    else
        echo -e "${RED}❌ Backup file is corrupted!${NC}"
        exit 1
    fi
}

# Function to list backups
list_backups() {
    echo -e "${YELLOW}📋 Available backups:${NC}"
    echo ""
    
    if [ -z "$(ls -A $BACKUP_DIR)" ]; then
        echo "No backups found"
        return
    fi
    
    ls -lh $BACKUP_DIR/full_backup_*.sql.gz 2>/dev/null || echo "No full backups"
    echo ""
    ls -lh $INCREMENTAL_DIR/*.sql.gz 2>/dev/null || echo "No incremental backups"
}

# Function to cleanup old backups
cleanup_old_backups() {
    echo -e "${YELLOW}🧹 Cleaning up backups older than $RETENTION_DAYS days...${NC}"
    
    find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +$RETENTION_DAYS -exec rm {} \;
    
    COUNT=$(find $BACKUP_DIR -type f -name "*.sql.gz" | wc -l)
    echo -e "${GREEN}✓ Retention cleanup completed. Remaining backups: $COUNT${NC}"
}

# Function to restore from backup
restore_from_backup() {
    local backup_file=$1
    
    echo -e "${RED}⚠️  RESTORE OPERATION - CAUTION!${NC}"
    echo "This will restore your database from: $backup_file"
    read -p "Continue? (type 'YES' to confirm): " -r
    echo
    
    if [[ ! $REPLY =~ ^YES$ ]]; then
        echo "Restore cancelled"
        return
    fi
    
    echo -e "${YELLOW}🔄 Restoring from backup...${NC}"
    
    if command -v docker &> /dev/null && docker ps | grep -q dwaraka_mess_db; then
        # Docker restore
        gunzip -c "$backup_file" | docker exec -i dwaraka_mess_db pg_restore \
            -U $DB_USER \
            -d $DB_NAME \
            -F custom \
            -v
    else
        # Direct restore
        gunzip -c "$backup_file" | pg_restore \
            -h $DB_HOST \
            -U $DB_USER \
            -d $DB_NAME \
            -F custom \
            -v
    fi
    
    echo -e "${GREEN}✓ Restore completed${NC}"
}

# Main script
case "${1:-full}" in
    full)
        perform_full_backup
        verify_backup "$FULL_BACKUP"
        cleanup_old_backups
        ;;
    incremental)
        perform_incremental_backup
        cleanup_old_backups
        ;;
    verify)
        if [ -z "$2" ]; then
            LATEST=$(ls -t $BACKUP_DIR/full_backup_*.sql.gz 2>/dev/null | head -1)
            verify_backup "$LATEST"
        else
            verify_backup "$2"
        fi
        ;;
    list)
        list_backups
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <backup_file>"
            list_backups
            exit 1
        fi
        restore_from_backup "$2"
        ;;
    *)
        echo "Usage: $0 {full|incremental|verify|list|restore}"
        echo ""
        echo "Examples:"
        echo "  $0 full              - Perform full backup"
        echo "  $0 incremental       - Perform incremental backup"
        echo "  $0 verify            - Verify latest backup"
        echo "  $0 list              - List all backups"
        echo "  $0 restore <file>    - Restore from backup file"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Backup operation completed!${NC}"
