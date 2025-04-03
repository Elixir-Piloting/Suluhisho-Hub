from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from bson import ObjectId
from datetime import datetime

bp = Blueprint('mod', __name__, url_prefix='/mod')

def mod_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_moderator:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@mod_required
def index():
    """
    Moderator dashboard showing reported content and mod actions.
    """
    # Get filter parameters
    status = request.args.get('status', 'reported')
    content_type = request.args.get('type', 'all')
    
    # Base query for posts
    posts_query = {'is_deleted': False}
    if status == 'reported':
        posts_query['is_reported'] = True
    elif status == 'pending':
        posts_query['status'] = 'pending'
    
    # Get content based on type
    reported_posts = []
    reported_comments = []
    reported_suggestions = []
    
    if content_type in ['all', 'posts']:
        reported_posts = list(current_app.db.posts.find(posts_query).sort('reported_at', -1))
        print(f"Found {len(reported_posts)} reported posts with query: {posts_query}")
    
    if content_type in ['all', 'comments']:
        comments_query = {'is_deleted': False, 'is_reported': True} if status == 'reported' else {'is_deleted': False}
        reported_comments = list(current_app.db.comments.find(comments_query).sort('reported_at', -1))
        print(f"Found {len(reported_comments)} reported comments")
    
    if content_type in ['all', 'suggestions']:
        suggestions_query = {'is_deleted': False, 'is_reported': True} if status == 'reported' else {'is_deleted': False}
        reported_suggestions = list(current_app.db.suggestions.find(suggestions_query).sort('reported_at', -1))
        reported_suggestions = list(current_app.db.suggestions.find(suggestions_query).sort('created_at', -1))
    
    # Get recent mod actions
    mod_actions = list(current_app.db.mod_actions.find().sort('created_at', -1).limit(20))
    
    # Get moderation stats
    stats = {
        'total_reports': current_app.db.posts.count_documents({'is_reported': True}),
        'pending_posts': current_app.db.posts.count_documents({'status': 'pending'}),
        'resolved_reports': current_app.db.mod_actions.count_documents({'action_type': 'resolve_report'}),
        'removed_content': current_app.db.mod_actions.count_documents({'action_type': 'remove_content'})
    }
    
    return render_template('mod/index.html',
                         reported_posts=reported_posts,
                         reported_comments=reported_comments,
                         reported_suggestions=reported_suggestions,
                         mod_actions=mod_actions,
                         stats=stats,
                         current_status=status,
                         current_type=content_type)

@bp.route('/posts/<post_id>/approve', methods=['POST'])
@mod_required
def approve_post(post_id):
    """Approve a post and mark it as verified."""
    post = current_app.db.posts.find_one_or_404({'_id': ObjectId(post_id)})
    
    # Update post status
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {
            '$set': {
                'status': 'verified',
                'verified_by': current_user.id,
                'verified_at': datetime.utcnow()
            }
        }
    )
    
    # Log the action
    current_app.db.mod_actions.insert_one({
        'moderator_id': current_user.id,
        'action_type': 'approve_post',
        'target_id': post_id,
        'target_type': 'post',
        'created_at': datetime.utcnow(),
        'details': f'Approved post: {post.get("title", "Unknown post")}'
    })
    
    flash('Post has been approved and marked as verified.', 'success')
    return redirect(url_for('mod.index'))

@bp.route('/posts/<post_id>/resolve', methods=['POST'])
@mod_required
def resolve_report(post_id):
    """Resolve a report without taking action."""
    post = current_app.db.posts.find_one_or_404({'_id': ObjectId(post_id)})
    
    # Update post
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {
            '$set': {
                'is_reported': False,
                'report_resolved_by': current_user.id,
                'report_resolved_at': datetime.utcnow()
            }
        }
    )
    
    # Log the action
    current_app.db.mod_actions.insert_one({
        'moderator_id': current_user.id,
        'action_type': 'resolve_report',
        'target_id': post_id,
        'target_type': 'post',
        'created_at': datetime.utcnow(),
        'details': f'Resolved report for post: {post.get("title", "Unknown post")}'
    })
    
    flash('Report has been resolved.', 'success')
    return redirect(url_for('mod.index'))

@bp.route('/posts/<post_id>/remove', methods=['POST'])
@mod_required
def remove_post(post_id):
    """
    Remove a post and log the action.
    """
    post = current_app.db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        abort(404)
    
    # Soft delete the post
    current_app.db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$set': {
            'is_deleted': True,
            'deleted_by': current_user.get_id(),
            'deleted_at': datetime.utcnow()
        }}
    )
    
    # Log the action
    action = {
        'moderator_id': current_user.get_id(),
        'action_type': 'remove_post',
        'target_id': post_id,
        'reason': request.form.get('reason'),
        'created_at': datetime.utcnow()
    }
    current_app.db.mod_actions.insert_one(action)
    
    flash('Post has been removed.', 'success')
    return redirect(url_for('mod.index'))

@bp.route('/comments/<comment_id>/remove', methods=['POST'])
@mod_required
def remove_comment(comment_id):
    """
    Remove a comment and log the action.
    """
    comment = current_app.db.comments.find_one({'_id': ObjectId(comment_id)})
    if not comment:
        abort(404)
    
    # Soft delete the comment
    current_app.db.comments.update_one(
        {'_id': ObjectId(comment_id)},
        {'$set': {
            'is_deleted': True,
            'deleted_by': current_user.get_id(),
            'deleted_at': datetime.utcnow()
        }}
    )
    
    # Log the action
    action = {
        'moderator_id': current_user.get_id(),
        'action_type': 'remove_comment',
        'target_id': comment_id,
        'reason': request.form.get('reason'),
        'created_at': datetime.utcnow()
    }
    current_app.db.mod_actions.insert_one(action)
    
    flash('Comment has been removed.', 'success')
    return redirect(url_for('mod.index'))

@bp.route('/suggestions/<suggestion_id>/remove', methods=['POST'])
@mod_required
def remove_suggestion(suggestion_id):
    """
    Remove a suggestion and log the action.
    """
    suggestion = current_app.db.suggestions.find_one({'_id': ObjectId(suggestion_id)})
    if not suggestion:
        abort(404)
    
    # Soft delete the suggestion
    current_app.db.suggestions.update_one(
        {'_id': ObjectId(suggestion_id)},
        {'$set': {
            'is_deleted': True,
            'deleted_by': current_user.get_id(),
            'deleted_at': datetime.utcnow()
        }}
    )
    
    # Log the action
    action = {
        'moderator_id': current_user.get_id(),
        'action_type': 'remove_suggestion',
        'target_id': suggestion_id,
        'reason': request.form.get('reason'),
        'created_at': datetime.utcnow()
    }
    current_app.db.mod_actions.insert_one(action)
    
    flash('Suggestion has been removed.', 'success')
    return redirect(url_for('mod.index')) 