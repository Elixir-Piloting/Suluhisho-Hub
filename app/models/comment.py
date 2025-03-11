from datetime import datetime
from bson import ObjectId

class Comment:
    def __init__(self, content, author_id, post_id, _id=None):
        self._id = _id if _id else ObjectId()
        self.content = content
        self.author_id = author_id
        self.post_id = post_id
        self.created_at = datetime.utcnow()
        self.likes = []
        self.is_deleted = False

    def to_dict(self):
        return {
            '_id': self._id,
            'content': self.content,
            'author_id': self.author_id,
            'post_id': self.post_id,
            'created_at': self.created_at,
            'likes': self.likes,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def from_dict(data):
        comment = Comment(
            content=data['content'],
            author_id=data['author_id'],
            post_id=data['post_id'],
            _id=data['_id']
        )
        comment.created_at = data.get('created_at', datetime.utcnow())
        comment.likes = data.get('likes', [])
        comment.is_deleted = data.get('is_deleted', False)
        return comment

    def add_like(self, user_id):
        if user_id not in self.likes:
            self.likes.append(user_id)
            return True
        return False

    def remove_like(self, user_id):
        if user_id in self.likes:
            self.likes.remove(user_id)
            return True
        return False 