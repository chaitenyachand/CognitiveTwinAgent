# auth.py
import hashlib
from passlib.context import CryptContext
import database_utils as db

# Setup password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def register_user(username, email, password):
    """Registers a new user."""
    if db.get_user_by_username(username):
        return False, "Username already exists."
    
    # In a real app, you'd also check the email
    
    password_hash = hash_password(password)
    user_id = db.create_user(username, email, password_hash)
    
    if user_id:
        return True, "User registered successfully."
    else:
        return False, "Registration failed. Please try again."

def login_user(username, password):
    """Logs in an existing user."""
    user = db.get_user_by_username(username)
    if not user:
        return False, None
    
    if not verify_password(password, user['password_hash']):
        return False, None
        
    return True, user