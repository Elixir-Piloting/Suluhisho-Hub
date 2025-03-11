from flask import current_app
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from functools import lru_cache

@lru_cache(maxsize=1000)
def geocode_location(location_str):
    """
    Convert a location string to coordinates (latitude, longitude).
    Results are cached to avoid repeated API calls.
    """
    try:
        geolocator = Nominatim(user_agent="suluhisho_hub")
        location = geolocator.geocode(location_str)
        if location:
            return {
                'lat': location.latitude,
                'lng': location.longitude,
                'address': location.address
            }
    except (GeocoderTimedOut, GeocoderServiceError):
        pass
    return None

def get_nearby_posts(db, lat, lng, radius_km=10):
    """
    Find posts within a given radius of a point.
    Uses MongoDB's geospatial queries.
    """
    return list(db.posts.find({
        'location': {
            '$geoWithin': {
                '$centerSphere': [[lng, lat], radius_km / 6371]  # 6371 is Earth's radius in km
            }
        },
        'is_deleted': False
    }).sort('created_at', -1))

def get_location_stats(db):
    """
    Get statistics about post distribution by location.
    """
    pipeline = [
        {'$match': {'is_deleted': False}},
        {'$group': {
            '_id': '$location_area',
            'count': {'$sum': 1},
            'resolved': {'$sum': {'$cond': [{'$eq': ['$status', 'resolved']}, 1, 0]}},
            'coordinates': {'$first': '$location'}
        }},
        {'$sort': {'count': -1}}
    ]
    
    return list(db.posts.aggregate(pipeline))

def create_location_index(db):
    """
    Ensure geospatial index exists on the posts collection.
    """
    db.posts.create_index([('location', '2dsphere')])

def format_post_for_map(post):
    """
    Format a post document for map display.
    """
    return {
        'id': str(post['_id']),
        'title': post['title'],
        'status': post['status'],
        'category': post['category'],
        'location': post['location'],
        'location_area': post['location_area'],
        'created_at': post['created_at'],
        'upvotes': len(post.get('upvotes', [])),
        'author_username': post['author_username']
    } 