from datetime import datetime
from bson import ObjectId
from slugify import slugify

class Post:
    def __init__(self, title, description, author_id, category, _id=None, 
                 images=None, location=None, status='unresolved', slug=None):
        self._id = _id if _id else ObjectId()
        self.title = title
        self.description = description
        self.author_id = author_id
        self.category = category
        self.images = images or []
        # Ensure location is in GeoJSON format
        self.location = location if (location and isinstance(location, dict) and 
                                   location.get('type') == 'Point' and 
                                   isinstance(location.get('coordinates'), list)) else None
        self.status = status
        self.slug = slug or slugify(title)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.upvotes = []
        self.comment_count = 0
        self.suggestion_count = 0
        self.is_deleted = False

    def to_dict(self):
        return {
            '_id': self._id,
            'title': self.title,
            'description': self.description,
            'author_id': self.author_id,
            'category': self.category,
            'images': self.images,
            'location': self.location,  # Already in GeoJSON format
            'status': self.status,
            'slug': self.slug,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'upvotes': self.upvotes,
            'comment_count': self.comment_count,
            'suggestion_count': self.suggestion_count,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def from_dict(data):
        post = Post(
            title=data['title'],
            description=data['description'],
            author_id=data['author_id'],
            category=data['category'],
            _id=data['_id'],
            images=data.get('images', []),
            location=data.get('location'),  # Will be validated in __init__
            status=data.get('status', 'unresolved'),
            slug=data.get('slug')
        )
        post.created_at = data.get('created_at', datetime.utcnow())
        post.updated_at = data.get('updated_at', datetime.utcnow())
        post.upvotes = data.get('upvotes', [])
        post.comment_count = data.get('comment_count', 0)
        post.suggestion_count = data.get('suggestion_count', 0)
        post.is_deleted = data.get('is_deleted', False)
        return post

    def add_upvote(self, user_id):
        if user_id not in self.upvotes:
            self.upvotes.append(user_id)
            return True
        return False

    def remove_upvote(self, user_id):
        if user_id in self.upvotes:
            self.upvotes.remove(user_id)
            return True
        return False

    def mark_resolved(self):
        self.status = 'resolved'
        self.updated_at = datetime.utcnow()

    def soft_delete(self):
        self.is_deleted = True
        self.updated_at = datetime.utcnow() 