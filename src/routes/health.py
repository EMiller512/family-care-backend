from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.health_data import db, HealthData, Alert, UserProfile, Question
import json
import random

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/data', methods=['GET'])
def get_health_data():
    """Get health data for a user"""
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 7))  # Default to 7 days
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Calculate date range - include the full current day
    end_date = datetime.utcnow() + timedelta(days=1)  # Add 1 day to include today
    start_date = end_date - timedelta(days=days+1)  # Adjust start date accordingly
    
    # Query health data
    health_data = HealthData.query.filter(
        HealthData.user_id == user_id,
        HealthData.timestamp >= start_date,
        HealthData.timestamp <= end_date
    ).order_by(HealthData.timestamp.asc()).all()
    
    return jsonify({
        'data': [item.to_dict() for item in health_data],
        'count': len(health_data)
    })

@health_bp.route('/health/data', methods=['POST'])
def add_health_data():
    """Add new health data entry"""
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        # Parse timestamp if provided, otherwise use current time
        timestamp = datetime.utcnow()
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        health_entry = HealthData(
            user_id=data['user_id'],
            timestamp=timestamp,
            heart_rate=data.get('heart_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            sleep_hours=data.get('sleep_hours'),
            sleep_quality=data.get('sleep_quality'),
            steps=data.get('steps'),
            activity_level=data.get('activity_level'),
            mood=data.get('mood'),
            notes=data.get('notes'),
            is_manual_entry=data.get('is_manual_entry', True),
            data_source=data.get('data_source', 'manual')
        )
        
        db.session.add(health_entry)
        db.session.commit()
        
        # Check for alerts after adding data
        check_and_create_alerts(data['user_id'], health_entry)
        
        # Commit alerts to database
        db.session.commit()
        
        return jsonify({
            'message': 'Health data added successfully',
            'data': health_entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@health_bp.route('/health/simulate', methods=['POST'])
def generate_simulated_data():
    """Generate simulated health data for demonstration"""
    data = request.get_json()
    user_id = data.get('user_id')
    days = data.get('days', 7)
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        # Clear existing simulated data for this user
        HealthData.query.filter(
            HealthData.user_id == user_id,
            HealthData.data_source == 'simulation'
        ).delete()
        
        # Generate simulated data
        generated_data = []
        now = datetime.utcnow()
        
        for day in range(days):
            date = now - timedelta(days=day)
            
            # Generate hourly data for today, daily summaries for other days
            if day == 0:
                # Today - hourly data
                for hour in range(24):
                    if hour <= now.hour:
                        timestamp = datetime(date.year, date.month, date.date().day, hour)
                        entry = generate_health_data_point(user_id, timestamp, hour)
                        generated_data.append(entry)
            else:
                # Previous days - daily summary
                timestamp = datetime(date.year, date.month, date.date().day, 12)
                entry = generate_health_data_point(user_id, timestamp, 12, is_daily_summary=True)
                generated_data.append(entry)
        
        # Add all entries to database
        for entry in generated_data:
            db.session.add(entry)
        
        db.session.commit()
        
        # Generate some alerts based on the simulated data
        generate_sample_alerts(user_id)
        
        return jsonify({
            'message': f'Generated {len(generated_data)} simulated health data entries',
            'count': len(generated_data)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@health_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts for a user"""
    user_id = request.args.get('user_id')
    include_dismissed = request.args.get('include_dismissed', 'false').lower() == 'true'
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    query = Alert.query.filter(Alert.user_id == user_id)
    
    if not include_dismissed:
        query = query.filter(Alert.is_dismissed == False)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(20).all()
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in alerts],
        'count': len(alerts)
    })

@health_bp.route('/alerts/<int:alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_dismissed = True
    alert.dismissed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Alert dismissed successfully'})

@health_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        db.session.delete(alert)
        db.session.commit()
        return jsonify({'message': 'Alert deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@health_bp.route('/status', methods=['GET'])
def get_overall_status():
    """Get overall health status for a user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Get recent alerts
    recent_alerts = Alert.query.filter(
        Alert.user_id == user_id,
        Alert.is_dismissed == False,
        Alert.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    # Determine overall status
    critical_alerts = [a for a in recent_alerts if a.alert_type == 'alert']
    warning_alerts = [a for a in recent_alerts if a.alert_type == 'warning']
    
    if critical_alerts:
        status = 'alert'
        message = 'Immediate attention required'
    elif len(warning_alerts) > 1:
        status = 'warning'
        message = 'Some patterns need attention'
    elif warning_alerts:
        status = 'warning'
        message = 'Some patterns need attention'
    else:
        status = 'good'
        message = 'Everything looks normal'
    
    # Get latest health data
    latest_data = HealthData.query.filter(
        HealthData.user_id == user_id
    ).order_by(HealthData.timestamp.desc()).first()
    
    return jsonify({
        'status': status,
        'message': message,
        'alert_counts': {
            'urgent': len(critical_alerts),
            'warning': len(warning_alerts),
            'info': len([a for a in recent_alerts if a.alert_type == 'info'])
        },
        'last_updated': latest_data.timestamp.isoformat() if latest_data else None
    })

def generate_health_data_point(user_id, timestamp, hour, is_daily_summary=False):
    """Generate a single health data point"""
    is_night_time = hour < 6 or hour > 22
    
    # Generate realistic values with some randomness
    heart_rate = max(60, min(100, int(72 + (random.random() - 0.5) * 20 + (-10 if is_night_time else 0))))
    
    systolic = max(90, min(160, int(120 + (random.random() - 0.5) * 30)))
    diastolic = max(60, min(100, int(80 + (random.random() - 0.5) * 20)))
    
    sleep_hours = round((6.5 + random.random() * 2), 1) if is_daily_summary else None
    sleep_quality = int(6 + random.random() * 4) if is_daily_summary else None
    
    if not is_night_time:
        activity_level = int(20 + random.random() * 60)
        steps = int(3000 + random.random() * 7000) if is_daily_summary else int((3000 + random.random() * 7000) / 16)
    else:
        activity_level = int(random.random() * 10)
        steps = int(random.random() * 100)
    
    return HealthData(
        user_id=user_id,
        timestamp=timestamp,
        heart_rate=heart_rate,
        blood_pressure_systolic=systolic,
        blood_pressure_diastolic=diastolic,
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
        steps=steps,
        activity_level=activity_level,
        data_source='simulation',
        is_manual_entry=False
    )

def check_and_create_alerts(user_id, health_data):
    """Check health data and create alerts if needed"""
    alerts_to_create = []
    
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile or not user_profile.alert_thresholds:
        # Use default thresholds if none are set for the user
        thresholds = {
            'heartRateMin': 60,
            'heartRateMax': 100,
            'bpSystolicMax': 140,
            'bpDiastolicMax': 90,
            'sleepHoursMin': 6,
            'activityLevelMin': 30
        }
    else:
        thresholds = json.loads(user_profile.alert_thresholds)

    # Heart rate alerts
    if health_data.heart_rate:
        if health_data.heart_rate > thresholds.get('heartRateMax', 100):
            alerts_to_create.append({
                'type': 'warning',
                'title': 'Elevated Heart Rate',
                'message': f'Heart rate is {health_data.heart_rate} bpm, above normal range (' + str(thresholds.get('heartRateMin', 60)) + '-' + str(thresholds.get('heartRateMax', 100)) + ' bpm)',
                'metric': 'heartRate',
                'value': str(health_data.heart_rate)
            })
        elif health_data.heart_rate < thresholds.get('heartRateMin', 60):
            alerts_to_create.append({
                'type': 'warning',
                'title': 'Low Heart Rate',
                'message': f'Heart rate is {health_data.heart_rate} bpm, below normal range (' + str(thresholds.get('heartRateMin', 60)) + '-' + str(thresholds.get('heartRateMax', 100)) + ' bpm)',
                'metric': 'heartRate',
                'value': str(health_data.heart_rate)
            })
    
    # Blood pressure alerts
    if health_data.blood_pressure_systolic and health_data.blood_pressure_diastolic:
        if health_data.blood_pressure_systolic > thresholds.get('bpSystolicMax', 140) or health_data.blood_pressure_diastolic > thresholds.get('bpDiastolicMax', 90):
            alerts_to_create.append({
                'type': 'alert',
                'title': 'High Blood Pressure',
                'message': f'Blood pressure is {health_data.blood_pressure_systolic}/{health_data.blood_pressure_diastolic}, above target range (' + str(thresholds.get('bpSystolicMax', 140)) + '/' + str(thresholds.get('bpDiastolicMax', 90)) + ') mmHg',
                'metric': 'bloodPressure',
                'value': f'{health_data.blood_pressure_systolic}/{health_data.blood_pressure_diastolic}'
            })
    
    # Sleep alerts
    if health_data.sleep_hours and health_data.sleep_hours < thresholds.get('sleepHoursMin', 6):
            alerts_to_create.append({
                'type': 'warning',
                'title': 'Insufficient Sleep',
                'message': f'Only {health_data.sleep_hours} hours of sleep, below minimum (' + str(thresholds.get('sleepHoursMin', 6)) + ') hours',
                'metric': 'sleep',
                'value': str(health_data.sleep_hours)
            })

    # Activity alerts
    if health_data.activity_level and health_data.activity_level < thresholds.get('activityLevelMin', 30):
            alerts_to_create.append({
                'type': 'warning',
                'title': 'Low Activity Level',
                'message': f'Activity level is {health_data.activity_level}, below minimum (' + str(thresholds.get('activityLevelMin', 30)) + ')',
                'metric': 'activity',
                'value': str(health_data.activity_level)
            })
    
    # Create alerts
    for alert_data in alerts_to_create:
        alert = Alert(
            user_id=user_id,
            alert_type=alert_data['type'],
            title=alert_data['title'],
            message=alert_data['message'],
            metric=alert_data['metric'],
            value=alert_data['value']
        )
        db.session.add(alert)

def generate_sample_alerts(user_id):
    """Generate some sample alerts for demonstration"""
    # Only generate alerts occasionally
    if random.random() < 0.3:  # 30% chance
        sample_alerts = [
            {
                'type': 'info',
                'title': 'Heart Rate Pattern Change',
                'message': 'Heart rate patterns show unusual variation',
                'metric': 'heartRate',
                'value': '15'
            },
            {
                'type': 'warning',
                'title': 'Low Activity Pattern',
                'message': 'Activity levels have been consistently low',
                'metric': 'activity',
                'value': '25'
            }
        ]
        
        for alert_data in sample_alerts:
            if random.random() < 0.5:  # 50% chance for each alert
                alert = Alert(
                    user_id=user_id,
                    alert_type=alert_data['type'],
                    title=alert_data['title'],
                    message=alert_data['message'],
                    metric=alert_data['metric'],
                    value=alert_data['value']
                )
                db.session.add(alert)



@health_bp.route("/alerts/create", methods=["POST"])
def create_alert_manual():
    """Manually create an alert for demonstration purposes"""
    data = request.get_json()

    user_id = data.get("user_id")
    alert_type = data.get("alert_type")
    title = data.get("title")
    message = data.get("message")
    metric = data.get("metric")
    value = data.get("value")

    if not all([user_id, alert_type, title, message]):
        return jsonify({"error": "user_id, alert_type, title, and message are required"}), 400

    try:
        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            title=title,
            message=message,
            metric=metric,
            value=value
        )
        db.session.add(alert)
        db.session.commit()
        return jsonify({"message": "Alert created successfully", "alert": alert.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500




@health_bp.route('/questions/response', methods=['POST'])
def save_question_response():
    """Save a question response and generate alerts if needed"""
    data = request.get_json()
    
    user_id = data.get('user_id')
    question_text = data.get('question')
    response = data.get('response')
    
    if not all([user_id, question_text, response]):
        return jsonify({'error': 'user_id, question, and response are required'}), 400
    
    try:
        # Save the question response
        question = Question(
            user_id=user_id,
            question_text=question_text,
            response=response,
            responded_at=datetime.utcnow()
        )
        db.session.add(question)
        
        # Analyze response and create alerts if needed
        alerts_created = analyze_question_response(user_id, question_text, response)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Response saved successfully',
            'question': question.to_dict(),
            'alerts_created': alerts_created
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@health_bp.route('/questions', methods=['GET'])
def get_question_responses():
    """Get question responses for a user"""
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 7))
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    questions = Question.query.filter(
        Question.user_id == user_id,
        Question.asked_at >= start_date
    ).order_by(Question.asked_at.desc()).all()
    
    return jsonify({
        'questions': [q.to_dict() for q in questions],
        'count': len(questions)
    })

def analyze_question_response(user_id, question_text, response):
    """Analyze question response and create alerts for concerning responses"""
    alerts_created = []
    
    # Map of concerning responses
    negative_responses = ['not great', 'not good', 'poor', 'no', 'not really', 'bad', 'terrible']
    positive_pain_responses = ['yes', 'yeah', 'yep', 'quite a bit', 'a lot', 'severe']
    response_lower = response.lower()
    
    # Check if response is concerning
    # For pain questions, "yes" is concerning; for other questions, negative words are concerning
    is_pain_question = 'pain' in question_text.lower() or 'discomfort' in question_text.lower()
    
    if is_pain_question:
        is_concerning = any(pos in response_lower for pos in positive_pain_responses)
    else:
        is_concerning = any(neg in response_lower for neg in negative_responses)
    
    if not is_concerning:
        return alerts_created
    
    # Create alerts based on question type
    if 'feeling' in question_text.lower() or 'how are you' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='warning',
            title='Wellness Check Concern',
            message=f'Parent reported feeling "{response}" when asked about their wellbeing',
            metric='mood',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('wellness')
        
    elif 'sleep' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='warning',
            title='Sleep Quality Concern',
            message=f'Parent reported "{response}" when asked about sleep',
            metric='sleep',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('sleep')
        
    elif 'pain' in question_text.lower() or 'discomfort' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='alert',
            title='Pain or Discomfort Reported',
            message=f'Parent reported "{response}" when asked about pain or discomfort',
            metric='pain',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('pain')
        
    elif 'medication' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='warning',
            title='Medication Adherence Concern',
            message=f'Parent reported "{response}" when asked about medications',
            metric='medication',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('medication')
        
    elif 'energy' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='warning',
            title='Low Energy Reported',
            message=f'Parent reported "{response}" energy level',
            metric='energy',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('energy')
        
    elif 'hydrat' in question_text.lower() or 'water' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='info',
            title='Hydration Reminder Needed',
            message=f'Parent reported "{response}" when asked about hydration',
            metric='hydration',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('hydration')
        
    elif 'walk' in question_text.lower() or 'exercise' in question_text.lower():
        alert = Alert(
            user_id=user_id,
            alert_type='info',
            title='Activity Level Concern',
            message=f'Parent reported "{response}" when asked about physical activity',
            metric='activity',
            value=response
        )
        db.session.add(alert)
        alerts_created.append('activity')
    
    return alerts_created

