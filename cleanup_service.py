"""
Cleanup Service for Dwaraka Mess Management System
Handles automatic cleanup of old records to prevent unlimited database growth
"""
from datetime import datetime, date, timedelta
from flask import current_app
from extensions import db
from models import (
    QRScan, Attendance, Subscription, LeaveRequest, 
    Announcement, Feedback, Order, Payment
)
import cloudinary_service


class CleanupService:
    """Service for cleaning up old database records."""
    
    @staticmethod
    def cleanup_old_qr_scans(months=12):
        """
        Delete QR scan records older than specified months.
        QR scans are used for daily attendance tracking and don't need long-term retention.
        
        Args:
            months: Delete records older than this many months (default: 12)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = date.today() - timedelta(days=months * 30)
            deleted = QRScan.query.filter(QRScan.scan_date < cutoff_date).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} QR scan records older than {cutoff_date}")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup QR scans: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_attendance(months=12):
        """
        Delete attendance records older than specified months.
        Keep only recent attendance for reporting purposes.
        
        Args:
            months: Delete records older than this many months (default: 12)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = date.today() - timedelta(days=months * 30)
            deleted = Attendance.query.filter(Attendance.date < cutoff_date).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} attendance records older than {cutoff_date}")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup attendance: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_subscriptions(months=24):
        """
        Delete expired subscription records older than specified months.
        Keep recent subscriptions for reference.
        
        Args:
            months: Delete records older than this many months (default: 24)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
            deleted = Subscription.query.filter(
                Subscription.status == 'expired',
                Subscription.created_at < cutoff_date
            ).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} old subscription records")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup subscriptions: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_leave_requests(months=12):
        """
        Delete old leave requests (approved/rejected) older than specified months.
        
        Args:
            months: Delete records older than this many months (default: 12)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
            deleted = LeaveRequest.query.filter(
                LeaveRequest.status.in_(['approved', 'rejected']),
                LeaveRequest.created_at < cutoff_date
            ).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} old leave requests")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup leave requests: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_announcements(days=90):
        """
        Delete inactive announcements older than specified days.
        
        Args:
            days: Delete inactive announcements older than this many days (default: 90)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = Announcement.query.filter(
                Announcement.is_active == False,
                Announcement.created_at < cutoff_date
            ).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} old inactive announcements")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup announcements: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_feedback(months=12):
        """
        Archive or delete old feedback older than specified months.
        
        Args:
            months: Delete feedback older than this many months (default: 12)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
            deleted = Feedback.query.filter(Feedback.created_at < cutoff_date).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} old feedback records")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup feedback: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_old_orders(months=6):
        """
        Delete completed/cancelled orders older than specified months.
        
        Args:
            months: Delete orders older than this many months (default: 6)
        
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
            deleted = Order.query.filter(
                Order.order_status.in_(['served', 'cancelled']),
                Order.created_at < cutoff_date
            ).delete()
            db.session.commit()
            current_app.logger.info(f"Cleaned up {deleted} old orders")
            return deleted
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup orders: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_orphaned_cloudinary_images():
        """
        Delete Cloudinary images that are not referenced in the database.
        This prevents storage waste from deleted/rejected payments.
        
        Returns:
            int: Number of images deleted
        """
        try:
            if not current_app.config.get('CLOUDINARY_ENABLED'):
                current_app.logger.info("Cloudinary not enabled, skipping orphan cleanup")
                return 0
            
            deleted_count = cloudinary_service.cleanup_orphaned_images()
            current_app.logger.info(f"Cleaned up {deleted_count} orphaned Cloudinary images")
            return deleted_count
        except Exception as e:
            current_app.logger.error(f"Failed to cleanup orphaned Cloudinary images: {str(e)}")
            return 0
    
    @staticmethod
    def cleanup_rejected_payments(days=30):
        """
        Delete rejected payment records older than specified days.
        Also deletes associated Cloudinary images.
        
        Args:
            days: Delete rejected payments older than this many days (default: 30)
        
        Returns:
            dict: Count of payments and images deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            rejected_payments = Payment.query.filter(
                Payment.status == 'rejected',
                Payment.created_at < cutoff_date
            ).all()
            
            images_deleted = 0
            if current_app.config.get('CLOUDINARY_ENABLED'):
                for payment in rejected_payments:
                    if payment.cloudinary_public_id:
                        if cloudinary_service.delete_payment_screenshot(payment.cloudinary_public_id):
                            images_deleted += 1
            
            payments_deleted = len(rejected_payments)
            for payment in rejected_payments:
                db.session.delete(payment)
            
            db.session.commit()
            current_app.logger.info(f"Cleaned up {payments_deleted} rejected payments and {images_deleted} images")
            return {'payments': payments_deleted, 'images': images_deleted}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup rejected payments: {str(e)}")
            return {'payments': 0, 'images': 0}
    
    @staticmethod
    def run_all_cleanup():
        """
        Run all cleanup operations with default settings.
        This should be scheduled to run periodically (e.g., weekly/monthly).
        
        Returns:
            dict: Summary of cleanup results
        """
        results = {
            'qr_scans': CleanupService.cleanup_old_qr_scans(months=12),
            'attendance': CleanupService.cleanup_old_attendance(months=12),
            'subscriptions': CleanupService.cleanup_old_subscriptions(months=24),
            'leave_requests': CleanupService.cleanup_old_leave_requests(months=12),
            'announcements': CleanupService.cleanup_old_announcements(days=90),
            'feedback': CleanupService.cleanup_old_feedback(months=12),
            'orders': CleanupService.cleanup_old_orders(months=6),
            'rejected_payments': CleanupService.cleanup_rejected_payments(days=30),
            'orphaned_images': CleanupService.cleanup_orphaned_cloudinary_images()
        }
        
        total_deleted = sum(
            v if isinstance(v, int) else sum(v.values()) 
            for v in results.values()
        )
        
        current_app.logger.info(f"Cleanup completed. Total records deleted: {total_deleted}")
        current_app.logger.info(f"Cleanup details: {results}")
        
        return results


def get_cleanup_candidates():
    """
    Get counts of records that would be deleted by cleanup operations.
    Useful for preview before running actual cleanup.
    
    Returns:
        dict: Count of records eligible for cleanup
    """
    today = date.today()
    now = datetime.utcnow()
    
    return {
        'qr_scans_old': QRScan.query.filter(
            QRScan.scan_date < today - timedelta(days=365)
        ).count(),
        'attendance_old': Attendance.query.filter(
            Attendance.date < today - timedelta(days=365)
        ).count(),
        'subscriptions_expired': Subscription.query.filter(
            Subscription.status == 'expired',
            Subscription.created_at < now - timedelta(days=730)
        ).count(),
        'leave_requests_old': LeaveRequest.query.filter(
            LeaveRequest.status.in_(['approved', 'rejected']),
            LeaveRequest.created_at < now - timedelta(days=365)
        ).count(),
        'announcements_inactive': Announcement.query.filter(
            Announcement.is_active == False,
            Announcement.created_at < now - timedelta(days=90)
        ).count(),
        'feedback_old': Feedback.query.filter(
            Feedback.created_at < now - timedelta(days=365)
        ).count(),
        'orders_old': Order.query.filter(
            Order.order_status.in_(['served', 'cancelled']),
            Order.created_at < now - timedelta(days=180)
        ).count(),
        'payments_rejected': Payment.query.filter(
            Payment.status == 'rejected',
            Payment.created_at < now - timedelta(days=30)
        ).count()
    }
