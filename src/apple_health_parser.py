#!/usr/bin/env python3
"""
Apple Health Data Parser for Family Care Monitor
Processes CSV exports from Apple Health/Watch data
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests

class AppleHealthParser:
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url
        self.parsed_data = []
        
    def parse_csv_file(self, csv_file_path: str) -> List[Dict]:
        """Parse Apple Health CSV export file"""
        parsed_records = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Parse the timestamp
                try:
                    timestamp = datetime.strptime(row['Date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
                
                # Extract health metrics
                record = {
                    'timestamp': timestamp.isoformat(),
                    'date': timestamp.date().isoformat(),
                    'time': timestamp.time().isoformat(),
                    'distance_miles': self._safe_float(row.get('Distance walking / running(mi)')),
                    'heart_rate': self._safe_float(row.get('Heart rate(count/min)')),
                    'resting_heart_rate': self._safe_float(row.get('Resting heart rate(count/min)')),
                    'step_count': self._safe_int(row.get('Step count(count)'))
                }
                
                # Only include records with at least one valid metric
                if any(record[key] is not None for key in ['heart_rate', 'resting_heart_rate', 'step_count', 'distance_miles']):
                    parsed_records.append(record)
        
        self.parsed_data = parsed_records
        return parsed_records
    
    def _safe_float(self, value: str) -> Optional[float]:
        """Safely convert string to float, return None if invalid"""
        if not value or value.strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int, return None if invalid"""
        if not value or value.strip() == '':
            return None
        try:
            return int(float(value))  # Handle cases like "1234.0"
        except (ValueError, TypeError):
            return None
    
    def aggregate_daily_data(self) -> List[Dict]:
        """Aggregate hourly data into daily summaries"""
        daily_data = {}
        
        for record in self.parsed_data:
            date = record['date']
            
            if date not in daily_data:
                daily_data[date] = {
                    'date': date,
                    'heart_rates': [],
                    'resting_heart_rates': [],
                    'total_steps': 0,
                    'total_distance': 0.0,
                    'records_count': 0
                }
            
            day_record = daily_data[date]
            
            # Collect heart rate data
            if record['heart_rate'] is not None:
                day_record['heart_rates'].append(record['heart_rate'])
            
            if record['resting_heart_rate'] is not None:
                day_record['resting_heart_rates'].append(record['resting_heart_rate'])
            
            # Sum steps and distance
            if record['step_count'] is not None:
                day_record['total_steps'] += record['step_count']
            
            if record['distance_miles'] is not None:
                day_record['total_distance'] += record['distance_miles']
            
            day_record['records_count'] += 1
        
        # Calculate daily averages and totals
        aggregated_data = []
        for date, data in daily_data.items():
            daily_summary = {
                'date': date,
                'avg_heart_rate': round(sum(data['heart_rates']) / len(data['heart_rates']), 1) if data['heart_rates'] else None,
                'avg_resting_heart_rate': round(sum(data['resting_heart_rates']) / len(data['resting_heart_rates']), 1) if data['resting_heart_rates'] else None,
                'total_steps': data['total_steps'],
                'total_distance_miles': round(data['total_distance'], 2),
                'activity_level': self._calculate_activity_level(data['total_steps'], data['total_distance']),
                'records_count': data['records_count']
            }
            aggregated_data.append(daily_summary)
        
        # Sort by date
        aggregated_data.sort(key=lambda x: x['date'])
        return aggregated_data
    
    def _calculate_activity_level(self, steps: int, distance: float) -> int:
        """Calculate activity level score (1-100) based on steps and distance"""
        # Base score from steps (0-70 points)
        step_score = min(steps / 10000 * 70, 70)  # 10k steps = 70 points
        
        # Additional score from distance (0-30 points)
        distance_score = min(distance * 10, 30)  # 3+ miles = 30 points
        
        return int(step_score + distance_score)
    
    def convert_to_health_api_format(self, daily_data: List[Dict], user_id: str = "2", make_relative: bool = True) -> List[Dict]:
        """Convert aggregated data to our health API format
        
        Args:
            daily_data: List of daily aggregated health data
            user_id: User ID for the API records
            make_relative: If True, adjust dates so most recent data is today
        """
        api_records = []
        
        # Calculate date offset if making dates relative
        date_offset_days = 0
        if make_relative and daily_data:
            from datetime import date, timedelta
            # Find the most recent date in the data
            most_recent_date = max(datetime.strptime(day['date'], '%Y-%m-%d').date() for day in daily_data)
            today = date.today()
            date_offset_days = (today - most_recent_date).days
        
        for day in daily_data:
            # Adjust date if making relative
            original_date = datetime.strptime(day['date'], '%Y-%m-%d').date()
            if make_relative:
                from datetime import timedelta
                adjusted_date = original_date + timedelta(days=date_offset_days)
                date_str = adjusted_date.isoformat()
            else:
                date_str = day['date']
            
            # Convert to our API format
            api_record = {
                'user_id': user_id,
                'date': date_str,
                'time': '12:00:00',  # Use noon as default time for daily data
                'heart_rate': day['avg_heart_rate'],  # Use snake_case to match backend
                'systolic_bp': None,  # Apple Watch doesn't measure BP
                'diastolic_bp': None,
                'sleep_hours': None,  # Not in this export
                'sleep_quality': None,
                'steps': day['total_steps'],
                'activity_level': day['activity_level'],
                'mood': None,
                'notes': f"Apple Watch data: {day['total_distance_miles']} miles, {day['records_count']} readings"
            }
            
            # Only include records with meaningful data
            if api_record['heart_rate'] or api_record['steps']:
                api_records.append(api_record)
        
        return api_records
    
    def upload_to_api(self, api_records: List[Dict]) -> List[Dict]:
        """Upload processed data to the health monitoring API"""
        results = []
        
        for record in api_records:
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/health/data",
                    json=record,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 201:
                    results.append({
                        'status': 'success',
                        'date': record['date'],
                        'response': response.json()
                    })
                else:
                    results.append({
                        'status': 'error',
                        'date': record['date'],
                        'error': response.text
                    })
            except Exception as e:
                results.append({
                    'status': 'error',
                    'date': record['date'],
                    'error': str(e)
                })
        
        return results
    
    def generate_summary_report(self, daily_data: List[Dict]) -> Dict:
        """Generate a summary report of the Apple Watch data"""
        if not daily_data:
            return {'error': 'No data to analyze'}
        
        # Calculate overall statistics
        heart_rates = [d['avg_heart_rate'] for d in daily_data if d['avg_heart_rate']]
        resting_heart_rates = [d['avg_resting_heart_rate'] for d in daily_data if d['avg_resting_heart_rate']]
        daily_steps = [d['total_steps'] for d in daily_data if d['total_steps']]
        activity_levels = [d['activity_level'] for d in daily_data if d['activity_level']]
        
        report = {
            'data_period': {
                'start_date': daily_data[0]['date'],
                'end_date': daily_data[-1]['date'],
                'total_days': len(daily_data)
            },
            'heart_rate_analysis': {
                'avg_heart_rate': round(sum(heart_rates) / len(heart_rates), 1) if heart_rates else None,
                'avg_resting_heart_rate': round(sum(resting_heart_rates) / len(resting_heart_rates), 1) if resting_heart_rates else None,
                'heart_rate_range': f"{min(heart_rates):.1f} - {max(heart_rates):.1f}" if heart_rates else None
            },
            'activity_analysis': {
                'avg_daily_steps': round(sum(daily_steps) / len(daily_steps)) if daily_steps else None,
                'total_steps': sum(daily_steps) if daily_steps else None,
                'avg_activity_level': round(sum(activity_levels) / len(activity_levels)) if activity_levels else None,
                'most_active_day': max(daily_data, key=lambda x: x['total_steps'])['date'] if daily_steps else None
            },
            'health_insights': self._generate_health_insights(daily_data)
        }
        
        return report
    
    def _generate_health_insights(self, daily_data: List[Dict]) -> List[str]:
        """Generate health insights based on the data patterns"""
        insights = []
        
        # Analyze heart rate patterns
        heart_rates = [d['avg_heart_rate'] for d in daily_data if d['avg_heart_rate']]
        if heart_rates:
            avg_hr = sum(heart_rates) / len(heart_rates)
            if avg_hr > 100:
                insights.append("⚠️ Average heart rate is elevated - consider medical consultation")
            elif avg_hr < 60:
                insights.append("ℹ️ Heart rate indicates good cardiovascular fitness")
            else:
                insights.append("✅ Heart rate patterns appear normal")
        
        # Analyze activity patterns
        daily_steps = [d['total_steps'] for d in daily_data if d['total_steps']]
        if daily_steps:
            avg_steps = sum(daily_steps) / len(daily_steps)
            if avg_steps < 5000:
                insights.append("⚠️ Daily step count is below recommended levels")
            elif avg_steps > 10000:
                insights.append("✅ Excellent daily activity levels maintained")
            else:
                insights.append("ℹ️ Moderate activity levels - room for improvement")
        
        # Check for consistency
        if len(set(d['date'] for d in daily_data)) >= 3:
            insights.append("✅ Consistent data collection over multiple days")
        
        return insights

def main():
    """Example usage of the Apple Health Parser"""
    parser = AppleHealthParser()
    
    # Parse the CSV file
    csv_file = "/home/ubuntu/upload/Export2.csv"
    raw_data = parser.parse_csv_file(csv_file)
    print(f"Parsed {len(raw_data)} raw health records")
    
    # Aggregate into daily summaries
    daily_data = parser.aggregate_daily_data()
    print(f"Aggregated into {len(daily_data)} daily summaries")
    
    # Generate summary report
    report = parser.generate_summary_report(daily_data)
    print("\n=== APPLE WATCH HEALTH SUMMARY ===")
    print(json.dumps(report, indent=2))
    
    # Convert to API format
    api_records = parser.convert_to_health_api_format(daily_data)
    print(f"\nConverted to {len(api_records)} API records")
    
    return parser, daily_data, api_records, report

if __name__ == "__main__":
    main()
