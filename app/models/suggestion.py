from datetime import datetime
from bson import ObjectId

class Suggestion:
    def __init__(self, content, author_id, post_id, _id=None):
        self._id = _id if _id else ObjectId()
        self.content = content
        self.author_id = author_id
        self.post_id = post_id
        self.created_at = datetime.utcnow()
        self.votes = []  # List of user IDs who voted for this suggestion
        self.is_deleted = False
        self.is_implemented = False

    def to_dict(self):
        return {
            '_id': self._id,
            'content': self.content,
            'author_id': self.author_id,
            'post_id': self.post_id,
            'created_at': self.created_at,
            'votes': self.votes,
            'is_deleted': self.is_deleted,
            'is_implemented': self.is_implemented
        }

    @staticmethod
    def from_dict(data):
        suggestion = Suggestion(
            content=data['content'],
            author_id=data['author_id'],
            post_id=data['post_id'],
            _id=data['_id']
        )
        suggestion.created_at = data.get('created_at', datetime.utcnow())
        suggestion.votes = data.get('votes', [])
        suggestion.is_deleted = data.get('is_deleted', False)
        suggestion.is_implemented = data.get('is_implemented', False)
        return suggestion

    def add_vote(self, user_id):
        if user_id not in self.votes:
            self.votes.append(user_id)
            return True
        return False

    def remove_vote(self, user_id):
        if user_id in self.votes:
            self.votes.remove(user_id)
            return True
        return False

    def mark_implemented(self):
        self.is_implemented = True 