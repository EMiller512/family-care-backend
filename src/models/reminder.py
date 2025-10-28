from datetime import datetime
from src.models.user import db

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # Parent user ID
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), default='active')  # active, completed
    reminder_type = db.Column(db.String(20), default='event')  # daily, event
    start_date = db.Column(db.Date)  # When reminder should start appearing
    last_completed_date = db.Column(db.Date)  # For daily reminders - track last completion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(50))  # Caregiver user ID
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'reminder_type': self.reminder_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'last_completed_date': self.last_completed_date.isoformat() if self.last_completed_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_active_reminders(user_id):
        """Get all active reminders for a user"""
        return Reminder.query.filter_by(
            user_id=user_id, 
            status='active'
        ).order_by(Reminder.created_at.desc()).all()
    
    @staticmethod
    def get_completed_reminders(user_id, days=14):
        """Get completed reminders within the last N days"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.status == 'completed',
            Reminder.completed_at >= cutoff_date
        ).order_by(Reminder.completed_at.desc()).all()
    
    def mark_completed(self):
        """Mark reminder as completed"""
        if self.reminder_type == 'daily':
            # For daily reminders, just update the last completed date
            from datetime import date
            self.last_completed_date = date.today()
        else:
            # For event reminders, mark as completed
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_daily_reminders(user_id):
        """Get all daily reminders for a user"""
        return Reminder.query.filter_by(
            user_id=user_id, 
            reminder_type='daily',
            status='active'
        ).order_by(Reminder.created_at.desc()).all()
    
    @staticmethod
    def get_active_reminders_for_today(user_id):
        """Get reminders that should be shown today"""
        from datetime import date
        today = date.today()
        
        # Get event reminders that are active and should start today or earlier
        event_reminders = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.reminder_type == 'event',
            Reminder.status == 'active',
            Reminder.start_date <= today
        ).all()
        
        # Get daily reminders that haven't been completed today
        daily_reminders = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.reminder_type == 'daily',
            Reminder.status == 'active',
            db.or_(
                Reminder.last_completed_date.is_(None),
                Reminder.last_completed_date < today
            )
        ).all()
        
        return event_reminders + daily_reminders
