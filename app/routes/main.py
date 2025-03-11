from flask import Blueprint, render_template, request, jsonify, current_app, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.post import Post
from datetime import datetime
from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Build query
    query = {'is_deleted': False}
    if category:
        query['category'] = category
    if status:
        query['status'] = status
    if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    # Get total count for pagination
    total = current_app.db.posts.count_documents(query)
    
    # Get posts with pagination
    posts = list(current_app.db.posts.find(query)
        .sort('created_at', -1)
        .skip((page - 1) * per_page)
        .limit(per_page))
    
    # Get author information for each post
    for post in posts:
        author_id = ObjectId(post['author_id'])
        author = current_app.db.users.find_one({'_id': author_id})
        post['author'] = {
            'username': author['username'] if author else '[deleted]',
            'profile_picture': author.get('profile_picture') if author else None
        }
    
    # Get categories for filter
    categories = current_app.db.posts.distinct('category')
    
    return render_template('main/index.html',
                         posts=posts,
                         categories=categories,
                         page=page,
                         per_page=per_page,
                         total=total,
                         search=search,
                         category=category,
                         status=status)

@bp.route('/profile/<username>')
def profile(username):
    """
    Redirect to the user profile view
    """
    return redirect(url_for('profile.view', username=username))

@bp.route('/account')
@login_required
def account():
    return render_template('main/account.html')

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            profile_picture = url_for('static', filename=f'uploads/{filename}')
            current_app.db.users.update_one(
                {'_id': current_user._id},
                {'$set': {'profile_picture': profile_picture}}
            )
    
    if 'email' in request.form:
        email = request.form['email']
        if email != current_user.email:
            # Check if email is already taken
            if current_app.db.users.find_one({'email': email, '_id': {'$ne': current_user._id}}):
                flash('Email already in use', 'error')
                return redirect(url_for('main.account'))
            
            current_app.db.users.update_one(
                {'_id': current_user._id},
                {'$set': {'email': email}}
            )
    
    flash('Profile updated successfully', 'success')
    return redirect(url_for('main.account'))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    user = current_app.db.users.find_one({'_id': current_user._id})
    
    if not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('main.account'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('main.account'))
    
    current_app.db.users.update_one(
        {'_id': current_user._id},
        {'$set': {'password_hash': generate_password_hash(new_password)}}
    )
    
    flash('Password updated successfully', 'success')
    return redirect(url_for('main.account'))

@bp.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    email_notifications = 'email_notifications' in request.form
    
    current_app.db.users.update_one(
        {'_id': current_user._id},
        {'$set': {'email_notifications': email_notifications}}
    )
    
    flash('Preferences updated successfully', 'success')
    return redirect(url_for('main.account'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get notifications with pagination
    notifications = list(current_app.db.notifications.find({
        'user_id': current_user.get_id(),
        'is_deleted': False
    }).sort('created_at', -1)
    .skip((page - 1) * per_page)
    .limit(per_page))
    
    # Mark notifications as read
    if notifications:
        current_app.db.notifications.update_many(
            {
                '_id': {'$in': [n['_id'] for n in notifications]},
                'is_read': False
            },
            {'$set': {'is_read': True}}
        )
    
    total = current_app.db.notifications.count_documents({
        'user_id': current_user.get_id(),
        'is_deleted': False
    })
    
    return render_template('main/notifications.html',
                         notifications=notifications,
                         page=page,
                         per_page=per_page,
                         total=total)

@bp.route('/map')
def map():
    # Get all posts with locations
    posts = list(current_app.db.posts.find({
        'location': {'$exists': True},
        'is_deleted': False
    }))
    
    markers = [{
        'id': str(post['_id']),
        'title': post['title'],
        'location': post['location'],
        'status': post['status']
    } for post in posts]
    
    return render_template('main/map.html', markers=markers)

@bp.route('/check-username')
def check_username():
    username = request.args.get('username')
    if not username:
        return jsonify({'available': False})
    
    user = current_app.db.users.find_one({'username': username})
    return jsonify({'available': user is None})

@bp.app_template_filter('timeago')
def timeago(date):
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now" 