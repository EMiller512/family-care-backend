#!/usr/bin/env python3
"""
Populate Apple Watch data for the past 14 days
"""

import sys
sys.path.insert(0, '/home/ubuntu/family-care-api')

from src.models.health_data import db, HealthData
from src.main import app
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

def generate_apple_watch_data():
    """Generate realistic Apple Watch data for the past 14 days"""
    
    with app.app_context():
        # Delete existing Apple Watch data for user_id=2
        HealthData.query.filter_by(user_id=2, data_source='apple_watch').delete()
        db.session.commit()
        
        print("Generating Apple Watch data for the past 14 days...")
        
        # Generate data for the past 14 days using Eastern timezone
        eastern = ZoneInfo('America/New_York')
        today = datetime.now(eastern).replace(hour=12, minute=0, second=0, microsecond=0)
        
        entries_created = 0
        
        for days_ago in range(13, -1, -1):  # 13 days ago to today (14 days total)
            date = today - timedelta(days=days_ago)
            
            # Generate realistic heart rate (60-75 bpm range for resting)
            heart_rate = random.randint(60, 75)
            
            # Generate realistic daily steps (4000-8500 range)
            steps = random.randint(4000, 8500)
            
            # Create entry
            entry = HealthData(
                user_id=2,
                timestamp=date,
                heart_rate=heart_rate,
                steps=steps,
                activity_level=random.randint(20, 60),
                data_source='apple_watch',
                is_manual_entry=False
            )
            
            db.session.add(entry)
            entries_created += 1
            
            print(f"  {date.date()}: HR={heart_rate} bpm, Steps={steps}")
        
        db.session.commit()
        
        print(f"\n✅ Successfully created {entries_created} Apple Watch data entries")
        print(f"Date range: {(today - timedelta(days=13)).date()} to {today.date()}")

if __name__ == '__main__':
    generate_apple_watch_data()

