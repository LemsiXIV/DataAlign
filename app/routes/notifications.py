from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.notification import Notification
from app.models.user import User
from app import db
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get user's notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(Notification.created_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'notifications': [notif.to_dict() for notif in notifications.items],
        'total': notifications.total,
        'pages': notifications.pages,
        'current_page': notifications.page,
        'has_next': notifications.has_next,
        'has_prev': notifications.has_prev
    })

@notifications_bp.route('/api/notifications/count')
@login_required
def get_notification_count():
    """Get count of unread notifications"""
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()
    
    return jsonify({'unread_count': unread_count})

@notifications_bp.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification marked as read'})

@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all user's notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All notifications marked as read'})

@notifications_bp.route('/api/notifications/<int:notification_id>/delete', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification deleted'})

@notifications_bp.route('/api/notifications/delete-read', methods=['DELETE'])
@login_required
def delete_all_read_notifications():
    """Delete all read notifications for the current user"""
    deleted_count = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=True
    ).delete()
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'{deleted_count} read notifications deleted',
        'deleted_count': deleted_count
    })

@notifications_bp.route('/test-admin-notifications')
@login_required
def test_admin_notifications():
    """Debug route to test admin notifications"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin required'}), 403
    
    try:
        # Get all admin users
        admin_users = User.query.filter_by(role='admin').all()
        admin_info = []
        
        for admin in admin_users:
            # Count notifications for this admin
            notification_count = Notification.query.filter_by(user_id=admin.id).count()
            admin_info.append({
                'id': admin.id,
                'username': admin.username,
                'role': admin.role,
                'notification_count': notification_count
            })
        
        # Create a test notification for all admins
        for admin in admin_users:
            create_notification(
                user_id=admin.id,
                title="Test Admin Notification",
                message="This is a test notification to verify the admin notification system is working.",
                notification_type='info'
            )
        
        return jsonify({
            'admin_users': admin_info,
            'test_notifications_created': len(admin_users)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/notifications')
@login_required
def notifications_page():
    """Notifications page"""
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                    .order_by(Notification.created_at.desc())\
                                    .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('notifications.html', notifications=notifications)

def create_notification(user_id, title, message, notification_type='info', related_request_id=None):
    """Helper function to create a notification"""
    try:
        print(f"DEBUG: Creating notification for user_id={user_id}, title='{title}', type='{notification_type}'")
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_request_id=related_request_id
        )
        db.session.add(notification)
        db.session.commit()
        
        print(f"DEBUG: Notification created successfully with ID: {notification.id}")
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"ERROR creating notification: {e}")
        import traceback
        traceback.print_exc()
        return None
