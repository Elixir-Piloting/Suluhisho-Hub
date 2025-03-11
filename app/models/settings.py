from datetime import datetime
from bson import ObjectId

class Settings:
    def __init__(self, data):
        self._id = data.get('_id', 'global')
        self.site_name = data.get('site_name', 'No More BS')
        self.site_description = data.get('site_description', 'A platform for constructive feedback')
        self.contact_email = data.get('contact_email', '')
        self.allow_registration = data.get('allow_registration', True)
        self.require_email_verification = data.get('require_email_verification', True)
        self.enable_email_notifications = data.get('enable_email_notifications', True)
        self.notify_moderators = data.get('notify_moderators', True)
        self.notify_admins = data.get('notify_admins', True)
        self.maintenance_mode = data.get('maintenance_mode', False)
        self.updated_at = data.get('updated_at', datetime.utcnow())

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        return {
            '_id': self._id,
            'site_name': self.site_name,
            'site_description': self.site_description,
            'contact_email': self.contact_email,
            'allow_registration': self.allow_registration,
            'require_email_verification': self.require_email_verification,
            'enable_email_notifications': self.enable_email_notifications,
            'notify_moderators': self.notify_moderators,
            'notify_admins': self.notify_admins,
            'maintenance_mode': self.maintenance_mode,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return cls({})
        return cls(data)

    @classmethod
    def get_maintenance_mode(cls, db):
        settings = db.settings.find_one({'_id': 'global'})
        if settings:
            return settings.get('maintenance_mode', False)
        return False

    @classmethod
    def get_all_settings(cls, db):
        settings = db.settings.find_one({'_id': 'global'})
        if settings:
            return cls.from_dict(settings)
        return cls({})

    def save(self, db):
        data = self.to_dict()
        data['updated_at'] = datetime.utcnow()
        db.settings.update_one(
            {'_id': self._id},
            {'$set': data},
            upsert=True
        )

    def __str__(self):
        return f"Settings (ID: {self._id})" 