import json
import os
import hashlib
USER_DB = "auth/users.json"
def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r") as f:
        return json.load(f)
def save_users(users):
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)  
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "email": email,
        "password": hash_password(password)
    }
    save_users(users)
    return True

def login_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True
    return False

def is_authenticated(username):
    return username in load_users()
