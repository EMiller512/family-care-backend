from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.reminder import Reminder

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/api/reminders', methods=['GET'])
def get_reminders():
    """Get reminders for a user"""
    user_id = request.args.get('user_id')
    status = request.args.get('status', 'all')  # all, active, completed
    reminder_type = request.args.get('type')  # daily, event
    today_only = request.args.get('today_only', 'false').lower() == 'true'
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        if today_only:
            reminders = Reminder.get_active_reminders_for_today(user_id)
        elif reminder_type == 'daily':
            reminders = Reminder.get_daily_reminders(user_id)
        elif reminder_type == 'event' and status == 'active':
            # Get only active event reminders (not daily)
            reminders = Reminder.query.filter_by(
                user_id=user_id,
                reminder_type='event',
                status='active'
            ).order_by(Reminder.created_at.desc()).all()
        elif status == 'active':
            reminders = Reminder.get_active_reminders(user_id)
        elif status == 'completed':
            reminders = Reminder.get_completed_reminders(user_id)
        else:
            # Get all reminders
            reminders = Reminder.query.filter_by(user_id=user_id).order_by(
                Reminder.created_at.desc()
            ).all()
        
        return jsonify({
            'reminders': [reminder.to_dict() for reminder in reminders]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/api/reminders', methods=['POST'])
def create_reminder():
    """Create a new reminder"""
    try:
        data = request.get_json()
        
        # Parse start_date if provided
        start_date = None
        if data.get('start_date'):
            from datetime import datetime
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        elif data.get('reminder_type') == 'daily':
            # For daily reminders, set start_date to today if not provided
            from datetime import date
            start_date = date.today()
        
        reminder = Reminder(
            user_id=data.get('user_id'),
            title=data.get('title'),
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            reminder_type=data.get('reminder_type', 'event'),
            start_date=start_date,
            created_by=data.get('created_by')
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'message': 'Reminder created successfully',
            'reminder': reminder.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/api/reminders/<int:reminder_id>/complete', methods=['PUT'])
def complete_reminder(reminder_id):
    """Mark a reminder as completed"""
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        reminder.mark_completed()
        
        return jsonify({
            'message': 'Reminder marked as completed',
            'reminder': reminder.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        db.session.delete(reminder)
        db.session.commit()
        
        return jsonify({'message': 'Reminder deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    """Update a reminder"""
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            reminder.title = data['title']
        if 'description' in data:
            reminder.description = data['description']
        if 'priority' in data:
            reminder.priority = data['priority']
        if 'reminder_type' in data:
            reminder.reminder_type = data['reminder_type']
        if 'start_date' in data:
            from datetime import datetime
            reminder.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reminder updated successfully',
            'reminder': reminder.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/api/reminders/seed', methods=['POST'])
def seed_reminders():
    """Seed some sample reminders for testing"""
    try:
        user_id = request.get_json().get('user_id', '2')  # Default to parent user
        
        sample_reminders = [
            {
                'title': 'Take Morning Medication',
                'description': 'Take blood pressure medication with breakfast',
                'priority': 'high'
            },
            {
                'title': 'Doctor Appointment Reminder',
                'description': 'Cardiology appointment tomorrow at 2:00 PM',
                'priority': 'high'
            },
            {
                'title': 'Weekly Exercise',
                'description': 'Go for a 30-minute walk in the neighborhood',
                'priority': 'medium'
            },
            {
                'title': 'Call Family',
                'description': 'Weekly check-in call with grandchildren',
                'priority': 'low'
            },
            {
                'title': 'Grocery Shopping',
                'description': 'Pick up fresh fruits and vegetables',
                'priority': 'medium'
            }
        ]
        
        for reminder_data in sample_reminders:
            reminder = Reminder(
                user_id=user_id,
                title=reminder_data['title'],
                description=reminder_data['description'],
                priority=reminder_data['priority'],
                created_by='1'  # Caregiver user ID
            )
            db.session.add(reminder)
        
        db.session.commit()
        
        return jsonify({'message': f'Created {len(sample_reminders)} sample reminders'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
