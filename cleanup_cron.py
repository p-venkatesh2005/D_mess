#!/usr/bin/env python3
"""
Scheduled Cleanup Job for Dwaraka Mess Management System

This script runs all cleanup operations to prevent database growth.
Designed to be executed by a cron job (Render Cron, GitHub Actions, etc.)

Usage:
    python cleanup_cron.py
"""
import sys
from datetime import datetime
from app import app
from cleanup_service import CleanupService


def main():
    """Execute all cleanup operations."""
    print("=" * 70)
    print("🧹 DWARAKA MESS - SCHEDULED CLEANUP")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with app.app_context():
            print("Running cleanup operations...")
            print("-" * 70)
            
            results = CleanupService.run_all_cleanup()
            
            print()
            print("=" * 70)
            print("📊 CLEANUP RESULTS")
            print("=" * 70)
            print(f"QR Scans (>12 months):        {results['qr_scans']} deleted")
            print(f"Attendance (>12 months):      {results['attendance']} deleted")
            print(f"Subscriptions (>24 months):   {results['subscriptions']} deleted")
            print(f"Leave Requests (>12 months):  {results['leave_requests']} deleted")
            print(f"Announcements (>90 days):     {results['announcements']} deleted")
            print(f"Feedback (>12 months):        {results['feedback']} deleted")
            print(f"Orders (>6 months):           {results['orders']} deleted")
            print(f"Rejected Payments (>30 days): {results['rejected_payments']['payments']} payments, "
                  f"{results['rejected_payments']['images']} images")
            print(f"Orphaned Cloudinary Images:   {results['orphaned_images']} deleted")
            print("=" * 70)
            
            total_deleted = sum(
                v if isinstance(v, int) else sum(v.values()) 
                for v in results.values()
            )
            
            print(f"\n✅ Total records deleted: {total_deleted}")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            return 0
    
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ CLEANUP FAILED")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
