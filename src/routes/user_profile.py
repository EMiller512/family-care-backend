from flask import Blueprint, request, jsonify
from src.models.health_data import db, UserProfile
import json

user_profile_bp = Blueprint("user_profile", __name__)

@user_profile_bp.route("/user_profile/<string:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile:
        return jsonify({"error": "User profile not found"}), 404
    return jsonify(user_profile.to_dict())

@user_profile_bp.route("/user_profile/<string:user_id>", methods=["PUT"])
def update_user_profile(user_id):
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile:
        return jsonify({"error": "User profile not found"}), 404

    data = request.get_json()

    if "name" in data:
        user_profile.name = data["name"]
    if "user_type" in data:
        user_profile.user_type = data["user_type"]
    if "monitored_user_id" in data:
        user_profile.monitored_user_id = data["monitored_user_id"]
    if "alert_thresholds" in data:
        user_profile.alert_thresholds = json.dumps(data["alert_thresholds"])

    try:
        db.session.commit()
        return jsonify(user_profile.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


