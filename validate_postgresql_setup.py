#!/usr/bin/env python
"""
Validation script to verify PostgreSQL migration is complete
Run: python validate_postgresql_setup.py
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"{GREEN}✓{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description} NOT FOUND: {filepath}")
        return False

def check_file_contains(filepath, search_text, description):
    """Check if a file contains specific text"""
    if not Path(filepath).exists():
        print(f"{RED}✗{RESET} {description}: File not found")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
        if search_text.lower() in content.lower():
            print(f"{GREEN}✓{RESET} {description}")
            return True
        else:
            print(f"{RED}✗{RESET} {description}")
            return False

def main():
    print(f"\n{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}PostgreSQL Migration Validation{RESET}")
    print(f"{BLUE}═══════════════════════════════════════════════════════════════{RESET}\n")
    
    checks = []
    
    # Check 1: Requirements updated
    print(f"{YELLOW}1. Checking requirements.txt{RESET}")
    checks.append(check_file_contains('requirements.txt', 'psycopg2', 
                                     'psycopg2-binary added to requirements'))
    checks.append(check_file_contains('requirements.txt', 'SQLAlchemy==2.0', 
                                     'SQLAlchemy 2.0 added to requirements'))
    
    # Check 2: Configuration updated
    print(f"\n{YELLOW}2. Checking config.py{RESET}")
    checks.append(check_file_contains('config.py', 'postgresql://', 
                                     'PostgreSQL connection string in config'))
    checks.append(check_file_contains('config.py', 'pool_size', 
                                     'Connection pooling configured'))
    checks.append(check_file_contains('config.py', 'pool_pre_ping', 
                                     'Pool pre-ping enabled'))
    
    # Check 3: Environment files
    print(f"\n{YELLOW}3. Checking environment configuration{RESET}")
    checks.append(check_file_exists('.env.example', 'Environment example'))
    checks.append(check_file_contains('.env.example', 'DB_HOST', 
                                     'PostgreSQL parameters in .env.example'))
    checks.append(check_file_exists('.env.production', 'Production environment template'))
    
    # Check 4: Docker setup
    print(f"\n{YELLOW}4. Checking Docker configuration{RESET}")
    checks.append(check_file_exists('docker-compose.yml', 'Docker Compose file'))
    checks.append(check_file_contains('docker-compose.yml', 'postgres', 
                                     'PostgreSQL service in docker-compose'))
    checks.append(check_file_exists('Dockerfile', 'Dockerfile'))
    
    # Check 5: Deployment scripts
    print(f"\n{YELLOW}5. Checking deployment scripts{RESET}")
    checks.append(check_file_exists('scripts/deploy_production.sh', 
                                   'Production deployment script'))
    checks.append(check_file_exists('scripts/backup_database.sh', 
                                   'Backup script'))
    
    # Check 6: Documentation
    print(f"\n{YELLOW}6. Checking documentation{RESET}")
    checks.append(check_file_exists('POSTGRESQL_MIGRATION.md', 
                                   'PostgreSQL migration guide'))
    checks.append(check_file_exists('SETUP_POSTGRES.md', 
                                   'PostgreSQL setup guide'))
    checks.append(check_file_exists('POSTGRESQL_SHIFT_COMPLETE.md', 
                                   'Migration completion summary'))
    
    # Check 7: Git configuration
    print(f"\n{YELLOW}7. Checking Git configuration{RESET}")
    checks.append(check_file_contains('.gitignore', '.env.production', 
                                     '.env files excluded from git'))
    checks.append(check_file_contains('.gitignore', 'backups/', 
                                     'Backups excluded from git'))
    
    # Check 8: Models compatibility
    print(f"\n{YELLOW}8. Checking SQLAlchemy models{RESET}")
    checks.append(check_file_contains('models.py', 'db.Model', 
                                     'Models are SQLAlchemy ORM compatible'))
    
    # Summary
    print(f"\n{BLUE}═══════════════════════════════════════════════════════════════{RESET}")
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  Total Checks: {total_checks}")
    print(f"  Passed: {GREEN}{passed_checks}{RESET}")
    print(f"  Failed: {RED}{total_checks - passed_checks}{RESET}")
    
    if all(checks):
        print(f"\n{GREEN}✅ All checks passed! PostgreSQL migration is complete.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print(f"  1. Update .env with your PostgreSQL credentials")
        print(f"  2. Run: docker-compose up -d")
        print(f"  3. Initialize database: docker exec -it dwaraka_mess_app python init_db.py")
        print(f"  4. Open browser: http://localhost:5000")
        print(f"\nFor detailed information, see: POSTGRESQL_MIGRATION.md")
        return 0
    else:
        print(f"\n{RED}❌ Some checks failed. Please review the migration.{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
