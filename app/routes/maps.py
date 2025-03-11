from flask import Blueprint, render_template, jsonify, request, current_app
from app.utils.maps import (
    geocode_location, get_nearby_posts, get_location_stats,
    create_location_index, format_post_for_map
)
from bson import ObjectId

bp = Blueprint('maps', __name__, url_prefix='/maps')

@bp.route('/')
def index():
    """
    Display the main map view.
    """
    return render_template('maps/index.html')

@bp.route('/data')
def get_map_data():
    """
    Get all posts with location data for the map.
    """
    posts = current_app.db.posts.find({
        'location': {'$exists': True},
        'is_deleted': False
    })
    
    return jsonify({
        'posts': [format_post_for_map(post) for post in posts]
    })

@bp.route('/nearby')
def get_nearby():
    """
    Get posts near a specific location.
    """
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        radius = float(request.args.get('radius', 10))  # Default 10km radius
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    posts = get_nearby_posts(current_app.db, lat, lng, radius)
    return jsonify({
        'posts': [format_post_for_map(post) for post in posts]
    })

@bp.route('/geocode')
def geocode():
    """
    Convert a location string to coordinates.
    """
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location is required'}), 400
    
    result = geocode_location(location)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Location not found'}), 404

@bp.route('/stats')
def location_stats():
    """
    Get statistics about post distribution by location.
    """
    stats = get_location_stats(current_app.db)
    return jsonify({'stats': stats})

@bp.route('/cluster')
def get_cluster():
    """
    Get posts in a specific area for clustering.
    """
    try:
        bounds = {
            'north': float(request.args.get('north')),
            'south': float(request.args.get('south')),
            'east': float(request.args.get('east')),
            'west': float(request.args.get('west'))
        }
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid bounds'}), 400
    
    posts = current_app.db.posts.find({
        'location': {
            '$geoWithin': {
                '$box': [
                    [bounds['west'], bounds['south']],
                    [bounds['east'], bounds['north']]
                ]
            }
        },
        'is_deleted': False
    })
    
    return jsonify({
        'posts': [format_post_for_map(post) for post in posts]
    }) 