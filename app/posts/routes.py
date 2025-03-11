from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import mongo
from bson import ObjectId

posts = Blueprint('posts', __name__)

@posts.route('/<post_id>/upvote', methods=['POST'])
@login_required
def upvote(post_id):
    try:
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
            
        user_id = current_user.get_id()
        upvotes = post.get('upvotes', [])
        
        if user_id in upvotes:
            # Remove upvote
            mongo.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$pull': {'upvotes': user_id}}
            )
            upvotes.remove(user_id)
        else:
            # Add upvote
            mongo.db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$addToSet': {'upvotes': user_id}}
            )
            upvotes.append(user_id)
            
        return jsonify({
            'upvotes': len(upvotes)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 