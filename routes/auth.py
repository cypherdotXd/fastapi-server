from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from pydantic import BaseModel, Field
from datetime import timedelta

from models.user import User
from utils import *
from db import *

auth_router = APIRouter(prefix="/auth")

# Define your secret key and algorithm for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"

# Dependency to get user from token
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    # Decode token
    username = token_to_username(token, secret_key=SECRET_KEY, algo=ALGORITHM)
    # Get user from decoded token data
    user = get_user_from_name(username=username)
    return user
    
# Login User
@auth_router.put("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print("trying log-in")
    user = get_user_from_name(form_data.username)
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    try:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(secret_key=SECRET_KEY, algorithm=ALGORITHM, data={"sub": user.username}, expires_delta=access_token_expires)
        print("login success")
        return {"id":user.id, "token":Token(access_token=access_token, token_type="bearer")}
        
    except Exception as e:
        print("error in login")
    return {"message":"Login Failed"}