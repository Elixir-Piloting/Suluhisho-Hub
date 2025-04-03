from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.models.post import Post
from app.utils.uploads import save_images
from app.utils.notifications import create_notification
from bson import ObjectId
from datetime import datetime
import json

bp = Blueprint('posts', __name__, url_prefix='/posts')

ALLOWED_CATEGORIES = [
    'Infrastructure',
    'Security',
    'Environment',
    'Public Services',
    'Transportation',
    'Education',
    'Healthcare',
    'Other'
]

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')  # JSON string with lat/lng
        images = request.files.getlist('images')
        
        if not title or not description or not category:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('posts.create'))
        
        if category not in ALLOWED_CATEGORIES:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('posts.create'))
        
        # Parse location JSON string into object
        location_obj = None
        if location:
            try:
                location_obj = json.loads(location)
                # Ensure location has the correct format for MongoDB
                if isinstance(location_obj, dict) and 'lat' in location_obj and 'lng' in location_obj:
                    location_obj = {
                        'type': 'Point',
                        'coordinates': [location_obj['lng'], location_obj['lat']]
                    }
            except json.JSONDecodeError:
                flash('Invalid location format', 'error')
                return redirect(url_for('posts.create'))
        
        # Handle image uploads
        image_paths = []
        if images:
            image_paths = save_images(images)
        
        # Create new post
        post = Post(
            title=title,
            description=description,
            author_id=current_user.get_id(),
            category=category,
            images=image_paths,
            location=location_obj
        )
        
        result = current_app.db.posts.insert_one(post.to_dict())
        flash('Post created successfully!', 'success')
        return redirect(url_for('posts.view', post_id=str(result.inserted_id)))
    
    return render_template('posts/create.html', categories=ALLOWED_CATEGORIES)

@bp.route('/<post_id>')
def view(post_id):
    try:
        # Ensure post_id is a valid ObjectId
        if not ObjectId.is_valid(post_id):
            print(f"Invalid ObjectId format: {post_id}")
            abort(404)
            
        post = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
        if not post:
            print(f"Post not found: {post_id}")
            abort(404)
        
        # Convert ObjectId to string for template
        post['_id'] = str(post['_id'])
        
        # Get author info
        author = current_app.db.users.find_one({'_id': ObjectId(post['author_id'])})
        if author:
            post['author'] = {
                'username': author['username'],
                'profile_picture': author.get('profile_picture')
            }
        else:
            post['author'] = {
                'username': '[deleted]',
                'profile_picture': None
            }
        
        # Initialize upvotes if not present
        if 'upvotes' not in post:
            post['upvotes'] = []
        
        # Convert upvote IDs to strings for template comparison
        post['upvotes'] = [str(uid) for uid in post['upvotes']]
        
        # Get comments with author information
        comments = list(current_app.db.comments.find({'post_id': ObjectId(post_id), 'is_deleted': False})
                       .sort('created_at', -1))
        
        # Get comment authors
        for comment in comments:
            comment_author = current_app.db.users.find_one({'_id': ObjectId(comment['author_id'])})
            comment['author'] = {
                'username': comment_author['username'] if comment_author else '[deleted]',
                'profile_picture': comment_author.get('profile_picture') if comment_author else None
            }
        
        # Get suggestions with author information
        suggestions = list(current_app.db.suggestions.find({'post_id': ObjectId(post_id), 'is_deleted': False})
                         .sort('created_at', -1))
        
        # Get suggestion authors
        for suggestion in suggestions:
            suggestion_author = current_app.db.users.find_one({'_id': ObjectId(suggestion['author_id'])})
            suggestion['author'] = {
                'username': suggestion_author['username'] if suggestion_author else '[deleted]',
                'profile_picture': suggestion_author.get('profile_picture') if suggestion_author else None
            }
        
        return render_template('posts/view.html',
                             post=post,
                             comments=comments,
                             suggestions=suggestions)
    except Exception as e:
        print(f"Error viewing post: {str(e)}")
        print(f"Post ID: {post_id}")
        abort(404)

@bp.route('/<post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post_data = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
    if not post_data:
        abort(404)
    
    post = Post.from_dict(post_data)
    
    # Check if user has permission to edit
    if post.author_id != current_user.get_id() and not current_user.is_moderator:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        images = request.files.getlist('images')
        
        if not title or not description or not category:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('posts.edit', post_id=post_id))
        
        if category not in ALLOWED_CATEGORIES:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('posts.edit', post_id=post_id))
        
        # Handle new image uploads
        new_image_paths = []
        if images:
            new_image_paths = save_images(images)
        
        # Update post
        update_data = {
            'title': title,
            'description': description,
            'category': category,
            'location': location if location else None,
            'updated_at': datetime.utcnow()
        }
        
        if new_image_paths:
            update_data['images'] = post.images + new_image_paths
        
        current_app.db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': update_data}
        )
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('posts.view', post_id=post_id))
    
    return render_template('posts/edit.html',
                         post=post,
                         categories=ALLOWED_CATEGORIES)

@bp.route('/<post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    post_data = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
    if not post_data:
        abort(404)
    
    post = Post.from_dict(post_data)
    
    # Check if user has permission to delete
    if post.author_id != current_user.get_id() and not current_user.is_moderator:
        abort(403)
    
    # Soft delete the post
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$set': {'is_deleted': True, 'updated_at': datetime.utcnow()}}
    )
    
    flash('Post deleted successfully.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/<post_id>/resolve', methods=['POST'])
@login_required
def resolve(post_id):
    post_data = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
    if not post_data:
        abort(404)
    
    post = Post.from_dict(post_data)
    
    # Check if user has permission to resolve
    if post.author_id != current_user.get_id() and not current_user.is_moderator:
        abort(403)
    
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$set': {'status': 'resolved', 'updated_at': datetime.utcnow()}}
    )
    
    flash('Post marked as resolved.', 'success')
    return redirect(url_for('posts.view', post_id=post_id))

@bp.route('/<post_id>/upvote', methods=['POST'])
@login_required
def upvote(post_id):
    try:
        if not ObjectId.is_valid(post_id):
            return jsonify({'error': 'Invalid post ID'}), 400
            
        post = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        user_id = ObjectId(current_user.get_id())
        upvotes = post.get('upvotes', [])
        
        # Initialize upvotes if it doesn't exist
        if 'upvotes' not in post:
            current_app.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': {'upvotes': []}}
            )
            upvotes = []
        
        # Convert existing upvotes to ObjectId for comparison
        upvotes = [ObjectId(uid) if isinstance(uid, str) else uid for uid in upvotes]
        
        if user_id in upvotes:
            # Remove upvote
            current_app.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$pull': {'upvotes': user_id}}
            )
        else:
            # Add upvote
            current_app.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$push': {'upvotes': user_id}}
            )
            # Create notification for post author
            if str(user_id) != post['author_id']:
                create_notification(
                    current_app.db,
                    post['author_id'],
                    f"{current_user.username} upvoted your post: {post['title']}",
                    'upvote',
                    post_id
                )
        
        # Return the updated count
        updated_post = current_app.db.posts.find_one({'_id': ObjectId(post_id)})
        return jsonify({'upvotes': len(updated_post.get('upvotes', []))})
    except Exception as e:
        print(f"Error upvoting post: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/<post_id>/comments', methods=['POST'])
@login_required
def add_comment(post_id):
    if not ObjectId.is_valid(post_id):
        abort(404)
        
    post = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
    if not post:
        abort(404)
    
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('posts.view', post_id=post_id))
    
    comment = {
        '_id': ObjectId(),
        'post_id': ObjectId(post_id),
        'author_id': ObjectId(current_user.get_id()),
        'content': content,
        'created_at': datetime.utcnow(),
        'is_deleted': False
    }
    
    current_app.db.comments.insert_one(comment)
    
    # Update comment count
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {'comment_count': 1}}
    )
    
    # Create notification for post author
    if str(current_user.get_id()) != post['author_id']:
        create_notification(
            current_app.db,
            post['author_id'],
            f"{current_user.username} commented on your post: {post['title']}",
            'comment',
            post_id
        )
    
    flash('Comment added successfully.', 'success')
    return redirect(url_for('posts.view', post_id=post_id))

@bp.route('/<post_id>/comments/<comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(post_id, comment_id):
    if not ObjectId.is_valid(post_id) or not ObjectId.is_valid(comment_id):
        abort(404)
    
    comment = current_app.db.comments.find_one({
        '_id': ObjectId(comment_id),
        'post_id': ObjectId(post_id),
        'is_deleted': False
    })
    
    if not comment:
        abort(404)
    
    # Check if user has permission to delete
    if str(comment['author_id']) != current_user.get_id() and not current_user.is_moderator:
        abort(403)
    
    # Soft delete the comment
    current_app.db.comments.update_one(
        {'_id': ObjectId(comment_id)},
        {'$set': {'is_deleted': True}}
    )
    
    # Update comment count
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {'comment_count': -1}}
    )
    
    flash('Comment deleted successfully.', 'success')
    return redirect(url_for('posts.view', post_id=post_id))

@bp.route('/<post_id>/suggestions', methods=['POST'])
@login_required
def add_suggestion(post_id):
    if not ObjectId.is_valid(post_id):
        abort(404)
        
    post = current_app.db.posts.find_one({'_id': ObjectId(post_id), 'is_deleted': False})
    if not post:
        abort(404)
    
    content = request.form.get('content')
    if not content:
        flash('Suggestion cannot be empty.', 'error')
        return redirect(url_for('posts.view', post_id=post_id))
    
    suggestion = {
        '_id': ObjectId(),
        'post_id': ObjectId(post_id),
        'author_id': ObjectId(current_user.get_id()),
        'content': content,
        'created_at': datetime.utcnow(),
        'is_deleted': False,
        'is_implemented': False
    }
    
    current_app.db.suggestions.insert_one(suggestion)
    
    # Update suggestion count
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {'suggestion_count': 1}}
    )
    
    # Create notification for post author
    if str(current_user.get_id()) != post['author_id']:
        create_notification(
            current_app.db,
            post['author_id'],
            f"{current_user.username} suggested a solution for your post: {post['title']}",
            'suggestion',
            post_id
        )
    
    flash('Suggestion added successfully.', 'success')
    return redirect(url_for('posts.view', post_id=post_id))

@bp.route('/<post_id>/suggestions/<suggestion_id>/delete', methods=['POST'])
@login_required
def delete_suggestion(post_id, suggestion_id):
    if not ObjectId.is_valid(post_id) or not ObjectId.is_valid(suggestion_id):
        abort(404)
    
    suggestion = current_app.db.suggestions.find_one({
        '_id': ObjectId(suggestion_id),
        'post_id': ObjectId(post_id),
        'is_deleted': False
    })
    
    if not suggestion:
        abort(404)
    
    # Check if user has permission to delete
    if str(suggestion['author_id']) != current_user.get_id() and not current_user.is_moderator:
        abort(403)
    
    # Soft delete the suggestion
    current_app.db.suggestions.update_one(
        {'_id': ObjectId(suggestion_id)},
        {'$set': {'is_deleted': True}}
    )
    
    # Update suggestion count
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {'suggestion_count': -1}}
    )
    
    flash('Suggestion deleted successfully.', 'success')
    return redirect(url_for('posts.view', post_id=post_id))

@bp.route('/report', methods=['POST'])
@login_required
def report():
    content_type = request.form.get('content_type')
    content_id = request.form.get('content_id')
    reason = request.form.get('reason')
    details = request.form.get('details')
    
    if not content_type or not content_id or not reason:
        flash('Please provide all required information.', 'error')
        return redirect(url_for('main.index'))
    
    # Create the report
    report_data = {
        'content_type': content_type,
        'content_id': ObjectId(content_id),
        'reporter_id': ObjectId(current_user.get_id()),
        'reporter_username': current_user.username,  # Add reporter's username
        'reason': reason,
        'details': details,
        'status': 'pending',
        'created_at': datetime.utcnow()
    }
    
    # Update the content to mark it as reported
    if content_type == 'post':
        current_app.db.posts.update_one(
            {'_id': ObjectId(content_id)},
            {
                '$set': {
                    'is_reported': True,
                    'reported_at': datetime.utcnow(),
                    'reported_by': current_user.id,
                    'reported_by_username': current_user.username,
                    'report_reason': reason
                }
            }
        )
    elif content_type == 'comment':
        current_app.db.comments.update_one(
            {'_id': ObjectId(content_id)},
            {
                '$set': {
                    'is_reported': True,
                    'reported_at': datetime.utcnow(),
                    'reported_by': current_user.id,
                    'reported_by_username': current_user.username,
                    'report_reason': reason
                }
            }
        )
    
    current_app.db.reports.insert_one(report_data)
    
    # Create notification for moderators
    moderators = list(current_app.db.users.find({'is_moderator': True}))
    for mod in moderators:
        create_notification(
            db=current_app.db,
            user_id=str(mod['_id']),
            content=f'A {content_type} has been reported. Reason: {reason}',
            related_type='report',
            related_id=content_id
        )
    
    flash('Content has been reported. Our moderators will review it.', 'success')
    
    # Redirect back to the post
    return redirect(url_for('posts.view', post_id=content_id)) 