from flask import current_app
from flask_mail import Message
from datetime import datetime
from bson import ObjectId

def create_notification(db, user_id, content, related_type=None, related_id=None):
    """
    Create a new notification for a user.
    """
    notification = {
        '_id': ObjectId(),
        'user_id': str(user_id),
        'content': content,
        'related_type': related_type,
        'related_id': str(related_id) if related_id else None,
        'created_at': datetime.utcnow(),
        'is_read': False,
        'is_deleted': False
    }
    
    db.notifications.insert_one(notification)
    return notification

def get_user_notifications(db, user_id, limit=20, skip=0, include_read=False):
    """
    Get user's notifications with pagination.
    """
    query = {
        'user_id': str(user_id),
        'is_deleted': False
    }
    if not include_read:
        query['is_read'] = False
    
    return list(db.notifications.find(query)
               .sort('created_at', -1)
               .skip(skip)
               .limit(limit))

def mark_notification_read(db, notification_id, user_id):
    """
    Mark a notification as read.
    """
    result = db.notifications.update_one(
        {
            '_id': ObjectId(notification_id),
            'user_id': str(user_id),
            'is_deleted': False
        },
        {'$set': {'is_read': True}}
    )
    return result.modified_count > 0

def mark_all_read(db, user_id):
    """
    Mark all notifications as read for a user.
    """
    result = db.notifications.update_many(
        {
            'user_id': str(user_id),
            'is_read': False
        },
        {'$set': {'is_read': True}}
    )
    return result.modified_count

def delete_notification(db, notification_id, user_id):
    """
    Delete a notification.
    """
    result = db.notifications.delete_one({
        '_id': ObjectId(notification_id),
        'user_id': str(user_id)
    })
    return result.deleted_count > 0

def notify_users(db, users, type, content, related_id=None, related_type=None, send_email=True):
    """
    Create notifications for multiple users and optionally send emails.
    """
    notifications = []
    for user in users:
        notification = create_notification(
            db, user['_id'], content, related_type, related_id
        )
        notifications.append(notification)
        
        if send_email and user.get('preferences', {}).get('email_notifications', True):
            send_notification_email(user['email'], type, content)
    
    return notifications

def send_notification_email(email, type, content):
    """
    Send an email notification.
    """
    subject_map = {
        'comment': 'New Comment on Your Post',
        'suggestion': 'New Suggestion on Your Post',
        'status_update': 'Your Post Status Updated',
        'upvote': 'Your Post Received an Upvote',
        'mention': 'You Were Mentioned in a Post',
        'resolution': 'Your Post Was Marked as Resolved'
    }
    
    msg = Message(
        subject=subject_map.get(type, 'New Notification'),
        recipients=[email],
        body=content,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    current_app.mail.send(msg)

def format_notification(notification):
    """
    Format a notification for JSON response.
    """
    return {
        '_id': str(notification['_id']),
        'content': notification['content'],
        'related_type': notification.get('related_type'),
        'related_id': notification.get('related_id'),
        'created_at': notification['created_at'].isoformat(),
        'is_read': notification.get('is_read', False)
    } 