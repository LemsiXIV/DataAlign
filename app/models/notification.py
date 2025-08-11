from app import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Remove FK for now
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    related_request_id = db.Column(db.Integer, nullable=True)  # Remove FK for now
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() + 'Z',  # Add Z to indicate UTC
            'related_request_id': self.related_request_id
        }
