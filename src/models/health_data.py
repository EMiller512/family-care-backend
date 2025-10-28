from src.models.user import db
from datetime import datetime
import json

class HealthData(db.Model):
    __tablename__ = 'health_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Vital signs
    heart_rate = db.Column(db.Integer)
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    
    # Sleep data
    sleep_hours = db.Column(db.Float)
    sleep_quality = db.Column(db.Integer)  # 1-10 scale
    
    # Activity data
    steps = db.Column(db.Integer)
    activity_level = db.Column(db.Integer)  # 1-100 scale
    
    # Additional data
    mood = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    # Metadata
    is_manual_entry = db.Column(db.Boolean, default=False)
    data_source = db.Column(db.String(50), default='manual')  # manual, simulation, device
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'heart_rate': self.heart_rate,
            'blood_pressure': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}" if self.blood_pressure_systolic and self.blood_pressure_diastolic else None,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'sleep_hours': self.sleep_hours,
            'sleep_quality': self.sleep_quality,
            'steps': self.steps,
            'activity_level': self.activity_level,
            'mood': self.mood,
            'notes': self.notes,
            'is_manual_entry': self.is_manual_entry,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    alert_type = db.Column(db.String(20), nullable=False)  # alert, warning, info
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    metric = db.Column(db.String(50))  # heartRate, bloodPressure, sleep, activity
    value = db.Column(db.String(50))
    threshold_data = db.Column(db.Text)  # JSON string of threshold info
    
    is_dismissed = db.Column(db.Boolean, default=False)
    is_acknowledged = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    dismissed_at = db.Column(db.DateTime)
    acknowledged_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'metric': self.metric,
            'value': self.value,
            'threshold_data': json.loads(self.threshold_data) if self.threshold_data else None,
            'is_dismissed': self.is_dismissed,
            'is_acknowledged': self.is_acknowledged,
            'timestamp': self.created_at.isoformat() if self.created_at else None,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # caregiver, parent
    
    # Caregiver-specific fields
    monitored_user_id = db.Column(db.String(100))  # ID of the parent they're monitoring
    
    # Threshold settings (JSON)
    alert_thresholds = db.Column(db.Text)  # JSON string of customizable thresholds
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'user_type': self.user_type,
            'monitored_user_id': self.monitored_user_id,
            'alert_thresholds': json.loads(self.alert_thresholds) if self.alert_thresholds else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    response = db.Column(db.String(100))
    
    asked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    responded_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_text': self.question_text,
            'response': self.response,
            'asked_at': self.asked_at.isoformat() if self.asked_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }

