from flask import Blueprint, render_template, jsonify, request, current_app, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.notifications import (
    get_user_notifications, mark_notification_read,
    mark_all_read, delete_notification, format_notification
)
from bson import ObjectId

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@bp.route('/')
@login_required
def index():
    """
    Display the notifications page.
    """
    return render_template('notifications/index.html')

@bp.route('/data')
@login_required
def get_notifications():
    """
    Get user's notifications.
    """
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    include_read = request.args.get('include_read') == 'true'
    
    notifications = get_user_notifications(
        current_app.db,
        current_user.get_id(),
        limit=per_page,
        skip=skip,
        include_read=include_read
    )
    
    total = current_app.db.notifications.count_documents({
        'user_id': str(current_user.get_id()),
        'is_read': {'$ne': True} if not include_read else {'$exists': True}
    })
    
    return jsonify({
        'notifications': [format_notification(n) for n in notifications],
        'total': total,
        'pages': (total + per_page - 1) // per_page
    })

@bp.route('/unread')
@login_required
def get_unread_count():
    """
    Get count of unread notifications.
    """
    count = current_app.db.notifications.count_documents({
        'user_id': str(current_user.get_id()),
        'is_read': False
    })
    
    return jsonify({'count': count})

@bp.route('/<notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """
    Mark a notification as read.
    """
    success = mark_notification_read(
        current_app.db,
        notification_id,
        current_user.get_id()
    )
    
    if not success:
        abort(404)
    
    return jsonify({'success': True})

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    try:
        current_app.db.notifications.update_many(
            {
                'user_id': current_user.get_id(),
                'is_read': False,
                'is_deleted': False
            },
            {'$set': {'is_read': True}}
        )
        flash('All notifications marked as read', 'success')
    except Exception as e:
        print(f"Error marking notifications as read: {str(e)}")
        flash('Error updating notifications', 'error')
    
    return redirect(url_for('main.notifications'))

@bp.route('/delete/<notification_id>', methods=['POST'])
@login_required
def delete(notification_id):
    try:
        # Find the notification
        notification = current_app.db.notifications.find_one({
            '_id': ObjectId(notification_id),
            'user_id': current_user.get_id()
        })
        
        if not notification:
            flash('Notification not found', 'error')
            return redirect(url_for('main.notifications'))
        
        # Soft delete the notification
        current_app.db.notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'is_deleted': True}}
        )
        
        flash('Notification deleted', 'success')
    except Exception as e:
        print(f"Error deleting notification: {str(e)}")
        flash('Error deleting notification', 'error')
    
    return redirect(url_for('main.notifications')) 