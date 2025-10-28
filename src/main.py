import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.health_data import HealthData, Alert, UserProfile, Question
from src.models.reminder import Reminder
from src.routes.user import user_bp
from src.routes.health import health_bp
from src.routes.user_profile import user_profile_bp
from src.routes.reminders import reminders_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes with explicit configuration
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False)

app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(user_profile_bp, url_prefix="/api")
app.register_blueprint(reminders_bp)
# uncomment if you need to use database
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/api/health')
def health_check():
    return {"status": "healthy"}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
