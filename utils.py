from bson import ObjectId
from fastapi import HTTPException, status
from typing import Annotated, Optional, Union
from datetime import datetime, timedelta
import bcrypt
import jwt
from jwt import PyJWTError

from db import *
from models.user import User

# Utility Functions
def get_user_from_name(username: str) -> Optional[User]:
    user_dict = users_collection.find_one({"username": username})
    if user_dict:
        try:
            user = User(**user_dict)
            return user
        except Exception as e:
            print("no user found")
            raise e
    else:
        return None
    

def get_user_model_from_db(id: str) -> Optional[User]:
    user_dict = users_collection.find_one({"_id": ObjectId(id)})
    if user_dict:
        return User(**user_dict)
    print("no user found")
    return None

# Hash a password using bcrypt
def hash_password(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    hashed_password = hashed_password.decode('utf-8')
    return hashed_password

# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password, hashed_password):
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password = password_byte_enc , hashed_password = hashed_password)

# Function to create access token
def create_access_token(data: dict, secret_key:str, algorithm:str, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def token_to_username(token:str, secret_key:str, algo:str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Decode token
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algo])
        username: str = payload.get("sub")
    except PyJWTError:
        print("JWT error")
        raise credentials_exception
    return username