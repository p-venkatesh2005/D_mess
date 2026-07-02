#!/usr/bin/env python3
"""
Migrate Existing Payment Screenshots from Local Storage to Cloudinary

This script migrates all existing payment screenshots stored locally
to Cloudinary cloud storage.

Usage:
    python migrate_to_cloudinary.py [--dry-run]

Options:
    --dry-run    Show what would be migrated without actually migrating
"""
import os
import sys
from app import app
from extensions import db
from models import Payment
import cloudinary_service


def migrate_existing_payments(dry_run=False):
    """
    Migrate all payments with local screenshot_path to Cloudinary.
    
    Args:
        dry_run: If True, only show what would be migrated
    """
    with app.app_context():
        # Find all payments with local paths but no Cloudinary URL
        payments_to_migrate = Payment.query.filter(
            Payment.screenshot_path.isnot(None),
            Payment.cloudinary_url.is_(None)
        ).all()
        
        total = len(payments_to_migrate)
        
        if total == 0:
            print("✅ No payments need migration. All are already on Cloudinary or have no screenshots.")
            return
        
        print(f"\n📦 Found {total} payments with local screenshots to migrate")
        print("=" * 70)
        
        if dry_run:
            print("\n🔍 DRY RUN - No files will be migrated\n")
            for idx, payment in enumerate(payments_to_migrate, 1):
                print(f"{idx}. Payment #{payment.id}")
                print(f"   Student: {payment.student.user.name}")
                print(f"   Amount: ₹{payment.amount}")
                print(f"   Status: {payment.status}")
                print(f"   Local path: {payment.screenshot_path}")
                print()
            print(f"\nRun without --dry-run to migrate these {total} payments")
            return
        
        # Actual migration
        print("\n🚀 Starting migration...\n")
        
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        for idx, payment in enumerate(payments_to_migrate, 1):
            print(f"[{idx}/{total}] Migrating Payment #{payment.id}...", end=" ")
            
            # Check if local file exists
            local_path = os.path.join(
                app.root_path,
                'static',
                payment.screenshot_path
            )
            
            if not os.path.exists(local_path):
                print(f"⚠️  SKIPPED (file not found: {local_path})")
                skipped_count += 1
                continue
            
            # Migrate to Cloudinary
            try:
                success = cloudinary_service.migrate_local_to_cloudinary(payment)
                if success:
                    db.session.commit()
                    print(f"✅ SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ FAILED")
                    fail_count += 1
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERROR: {str(e)}")
                fail_count += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully migrated: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️  Skipped (file not found): {skipped_count}")
        print(f"📦 Total processed: {total}")
        print("=" * 70)
        
        if success_count > 0:
            print(f"\n✨ {success_count} payments successfully migrated to Cloudinary!")
            print("\n💡 NEXT STEPS:")
            print("1. Verify uploads in Cloudinary dashboard")
            print("2. Test payment screenshots display correctly")
            print("3. Once verified, you can delete local files:")
            print(f"   rm -rf {os.path.join(app.root_path, 'static', 'uploads', 'payments')}")
        
        if fail_count > 0:
            print(f"\n⚠️  {fail_count} payments failed to migrate.")
            print("   Check the logs above for error details.")
            print("   You can re-run this script to retry failed migrations.")


def check_cloudinary_config():
    """Check if Cloudinary is properly configured."""
    with app.app_context():
        if not app.config.get('CLOUDINARY_ENABLED'):
            print("❌ ERROR: Cloudinary is not configured!")
            print("\nPlease set the following environment variables:")
            print("  CLOUDINARY_CLOUD_NAME")
            print("  CLOUDINARY_API_KEY")
            print("  CLOUDINARY_API_SECRET")
            print("\nSee STORAGE_OPTIMIZATION_IMPLEMENTATION.md for details.")
            return False
        
        print("✅ Cloudinary is configured")
        print(f"   Cloud Name: {app.config.get('CLOUDINARY_CLOUD_NAME')}")
        print(f"   Folder: {app.config.get('CLOUDINARY_FOLDER', 'd_mess')}")
        return True


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv
    
    print("\n" + "=" * 70)
    print("🔄 PAYMENT SCREENSHOT MIGRATION TO CLOUDINARY")
    print("=" * 70)
    
    # Check Cloudinary configuration
    if not check_cloudinary_config():
        sys.exit(1)
    
    # Run migration
    try:
        migrate_existing_payments(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
