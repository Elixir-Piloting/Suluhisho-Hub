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
    # Get reported content
    reported_posts = list(current_app.db.posts.find({
        'is_reported': True,
        'is_deleted': False
    }).sort('reported_at', -1))
    
    reported_comments = list(current_app.db.comments.find({
        'is_reported': True,
        'is_deleted': False
    }).sort('reported_at', -1))
    
    reported_suggestions = list(current_app.db.suggestions.find({
        'is_reported': True,
        'is_deleted': False
    }).sort('reported_at', -1))
    
    # Get recent mod actions
    mod_actions = list(current_app.db.mod_actions.find().sort('created_at', -1).limit(20))
    
    return render_template('mod/index.html',
                         reported_posts=reported_posts,
                         reported_comments=reported_comments,
                         reported_suggestions=reported_suggestions,
                         mod_actions=mod_actions)

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