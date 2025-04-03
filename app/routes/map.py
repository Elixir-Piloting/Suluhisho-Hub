from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required
from bson import ObjectId

bp = Blueprint('map', __name__, url_prefix='/map')

@bp.route('/')
def index():
    return render_template('map/index.html')

@bp.route('/posts')
def get_posts():
    """Get all posts with location data for the map"""
    posts = current_app.db.posts.find(
        {
            'location': {'$exists': True},
            'is_deleted': False
        },
        {
            '_id': 1,
            'title': 1,
            'description': 1,
            'status': 1,
            'location': 1,
            'created_at': 1
        }
    )
    
    posts_list = []
    for post in posts:
        # Only include posts that have valid location data
        if post.get('location') and 'coordinates' in post['location']:
            post['_id'] = str(post['_id'])  # Convert ObjectId to string
            # Truncate description
            if 'description' in post:
                post['description'] = post['description'][:100] + '...' if len(post['description']) > 100 else post['description']
            posts_list.append(post)
    
    return jsonify(posts_list)
