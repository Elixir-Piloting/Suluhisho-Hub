from datetime import datetime
from bson import ObjectId

class Report:
    def __init__(self, data):
        self._id = data.get('_id', ObjectId())
        self.content_type = data.get('content_type')
        self.content_id = data.get('content_id')
        self.reporter_id = data.get('reporter_id')
        self.reason = data.get('reason')
        self.status = data.get('status', 'pending')
        self.created_at = data.get('created_at', datetime.utcnow())
        self.handled_by = data.get('handled_by')
        self.handled_at = data.get('handled_at')
        self.title = data.get('title')

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        return {
            '_id': self._id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'reporter_id': self.reporter_id,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at,
            'handled_by': self.handled_by,
            'handled_at': self.handled_at,
            'title': self.title
        }

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        return cls(data)

    @classmethod
    def get_pending_count(cls, db):
        return db.reports.count_documents({'status': 'pending'})

    @classmethod
    def get_recent_reports(cls, db, limit=10):
        return list(db.reports.find({'status': 'pending'})
                   .sort('created_at', -1)
                   .limit(limit))

    def __str__(self):
        return f"Report for {self.content_type} {self.content_id} by {self.reporter_id}" 