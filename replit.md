# Family Care Monitor

## Overview
Family Care Monitor is a home health monitoring application built with Flask (backend) and React (frontend). It helps family caregivers monitor and care for family members by tracking health data, managing reminders, and providing health alerts.

**Current State**: Fully functional and ready to use. Successfully imported and configured for Replit environment on October 28, 2025.

## Recent Changes
- **October 28, 2025**: Initial import and setup
  - Installed Python 3.11 and all dependencies from requirements.txt
  - Modified Flask app to serve static React frontend files
  - Configured workflow to run on port 5000
  - Set up deployment configuration using Gunicorn with autoscale mode
  - Created .gitignore for Python project

## Project Architecture

### Technology Stack
- **Backend**: Flask 3.1.1 with Flask-CORS and Flask-SQLAlchemy
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Pre-built React application (static files)
- **Production Server**: Gunicorn

### Directory Structure
```
.
├── src/
│   ├── database/           # SQLite database files
│   ├── models/            # SQLAlchemy models (User, HealthData, Reminder)
│   ├── routes/            # API route handlers
│   │   ├── health.py
│   │   ├── reminders.py
│   │   ├── user.py
│   │   └── user_profile.py
│   ├── static/            # React frontend build files
│   │   ├── assets/        # JS and CSS bundles
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── main.py            # Flask application entry point
│   └── apple_health_parser.py
├── requirements.txt       # Python dependencies
├── Procfile              # Original deployment config
└── render.yaml           # Original Render.com config
```

### Key Features
- **Role-based access**: Family Caregiver and Parent/Senior roles
- **Health data tracking**: Monitor health metrics and alerts
- **Reminder system**: Manage care-related reminders
- **User profiles**: Store and view health information
- **RESTful API**: All routes prefixed with `/api/`

### Database
- Uses SQLite database at `src/database/app.db`
- Auto-creates tables on application startup
- Models: User, HealthData, Alert, UserProfile, Question, Reminder

### Configuration
- **Development**: Flask development server on 0.0.0.0:5000
- **Production**: Gunicorn with autoscale deployment
- **CORS**: Enabled for all `/api/*` routes
- **Static Files**: React app served from root path, API routes under `/api/`

## Running the Application
- **Development**: The workflow "Server" runs `python src/main.py`
- **Port**: 5000 (configured for Replit environment)
- **Deployment**: Configured for autoscale deployment with Gunicorn

## API Endpoints
- `GET /api/health` - Health check endpoint
- `/api/*` - Various health monitoring and user management endpoints
- All other routes serve the React frontend

## Notes
- The application includes Apple Health data parsing functionality
- Demo version notice displayed on frontend
- CORS configured to allow cross-origin requests for API endpoints
