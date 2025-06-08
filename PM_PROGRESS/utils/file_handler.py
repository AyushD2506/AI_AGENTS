# utils/file_handler.py
import os
import json
from datetime import datetime

DATA_DIR = "data/projects"


def ensure_user_dir(username):
    user_path = os.path.join(DATA_DIR, username)
    os.makedirs(user_path, exist_ok=True)
    return user_path


def create_project(username, project_name, description):
    user_path = ensure_user_dir(username)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_id = f"project_{timestamp}.json"
    project_data = {
        "project_id": project_id,
        "project_name": project_name,
        "description": description,
        "created_on": datetime.now().strftime("%Y-%m-%d"),
        "logs": []
    }
    with open(os.path.join(user_path, project_id), "w") as f:
        json.dump(project_data, f, indent=4)


def load_user_projects(username):
    user_path = os.path.join(DATA_DIR, username)
    if not os.path.exists(user_path):
        return []
    projects = []
    for file in os.listdir(user_path):
        if file.endswith(".json"):
            with open(os.path.join(user_path, file), "r") as f:
                projects.append(json.load(f))
    return sorted(projects, key=lambda x: x["created_on"], reverse=True)
