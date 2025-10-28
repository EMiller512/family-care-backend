# Family Care Monitor

## Overview
Family Care Monitor is a health monitoring application for families. This is a Flask-based backend API that manages user profiles, health data, alerts, and reminders for family caregivers and their loved ones.

**Current State:** Backend API is set up and running. Frontend will be imported in a later step.

**Last Updated:** October 28, 2025

## Recent Changes
- October 28, 2025: Initial setup in Replit environment
  - Installed Python 3.11 and Flask dependencies
  - Configured Flask backend to run on port 5000
  - Set up SQLite database with SQLAlchemy ORM
  - Configured deployment settings with Gunicorn
  - Added .gitignore for Python projects

## Project Architecture

### Backend (Flask)
- **Framework:** Flask 3.1.1
- **Database:** SQLite with SQLAlchemy ORM
- **API Routes:**
  - `/api/health` - Health check endpoint
  - `/api/*` - User, health data, profiles, and reminders endpoints
- **Port:** 5000 (development server)
- **Database Location:** `src/database/app.db`

### Models
- `User` - User accounts and authentication
- `HealthData` - Health metrics and records
- `Alert` - Health alerts and notifications
- `UserProfile` - User profile information
- `Question` - Health questionnaire data
- `Reminder` - Medication and appointment reminders

### Frontend
- **Status:** Not yet imported (old static files exist but will be replaced)
- **Will be added:** In a later step

## Configuration

### Development
- **Server:** Flask development server
- **Host:** 0.0.0.0:5000
- **Debug Mode:** Enabled
- **CORS:** Enabled for all `/api/*` routes

### Deployment
- **Target:** Autoscale (stateless web application)
- **Server:** Gunicorn with reuse-port enabled
- **Command:** `gunicorn --bind=0.0.0.0:5000 --reuse-port src.main:app`

## File Structure
```
├── src/
│   ├── models/          # Database models
│   ├── routes/          # API route blueprints
│   ├── database/        # SQLite database files
│   ├── static/          # Old frontend (to be replaced)
│   └── main.py          # Flask application entry point
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore patterns
└── Procfile            # Legacy deployment config
```

## Dependencies
- Flask 3.1.1
- Flask-CORS 6.0.0
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.41
- Gunicorn 21.2.0

## Notes
- The backend uses SQLite for simplicity but can be migrated to PostgreSQL if needed
- CORS is configured to allow all origins for development
- The static folder contains old frontend code that will be replaced when the new frontend is imported
