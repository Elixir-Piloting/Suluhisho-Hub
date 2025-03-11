from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.utils.uploads import save_images, delete_image
from werkzeug.security import check_password_hash
from bson import ObjectId
from datetime import datetime

bp = Blueprint('profile', __name__, url_prefix='/u')

@bp.route('/<username>')
def view(username):
    user = current_app.db.users.find_one({'username': username})
    if not user:
        abort(404)
    
    # Get user's posts
    posts = list(current_app.db.posts.find({
        'author_id': str(user['_id']),
        'is_deleted': False
    }).sort('created_at', -1))
    
    # Get comment and suggestion counts for each post
    for post in posts:
        post['comment_count'] = current_app.db.comments.count_documents({
            'post_id': post['_id'],
            'is_deleted': False
        })
        post['suggestion_count'] = current_app.db.suggestions.count_documents({
            'post_id': post['_id'],
            'is_deleted': False
        })
    
    # Get user statistics
    post_count = current_app.db.posts.count_documents({
        'author_id': str(user['_id']),
        'is_deleted': False
    })
    
    suggestion_count = current_app.db.suggestions.count_documents({
        'author_id': str(user['_id']),
        'is_deleted': False
    })
    
    # Format join date
    join_date = user.get('created_at', datetime.utcnow())
    
    return render_template('profile/view.html',
                         user=user,
                         posts=posts,
                         post_count=post_count,
                         suggestion_count=suggestion_count,
                         join_date=join_date)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            profile_picture = request.files.get('profile_picture')
            
            update_data = {
                'full_name': full_name,
                'email': email
            }
            
            # Handle profile picture upload
            if profile_picture:
                image_paths = save_images([profile_picture])
                if image_paths:
                    # Delete old profile picture if it exists
                    if current_user.profile_picture:
                        delete_image(current_user.profile_picture)
                    update_data['profile_picture'] = image_paths[0]
            
            current_app.db.users.update_one(
                {'_id': ObjectId(current_user.get_id())},
                {'$set': update_data}
            )
            
            flash('Profile updated successfully!', 'success')
            
        elif action == 'update_password':
            # Update password
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('profile.settings'))
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('profile.settings'))
            
            current_user.set_password(new_password)
            current_app.db.users.update_one(
                {'_id': ObjectId(current_user.get_id())},
                {'$set': {'password_hash': current_user.password_hash}}
            )
            
            flash('Password updated successfully!', 'success')
            
        elif action == 'update_preferences':
            # Update notification preferences
            email_notifications = request.form.get('email_notifications') == 'on'
            profile_visibility = request.form.get('profile_visibility', 'public')
            
            current_app.db.users.update_one(
                {'_id': ObjectId(current_user.get_id())},
                {'$set': {
                    'preferences': {
                        'email_notifications': email_notifications,
                        'profile_visibility': profile_visibility
                    }
                }}
            )
            
            flash('Preferences updated successfully!', 'success')
        
        return redirect(url_for('profile.settings'))
    
    return render_template('profile/settings.html') 