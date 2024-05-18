from fastapi import Body, Depends, HTTPException, UploadFile, File, status, APIRouter
from pydantic import BaseModel, Field
from models.user import User
from models.project import Project
import cloudinary
import cloudinary.uploader

from routes.auth import get_current_user
from utils import *
from db import *

# Cloudinary configuration
cloudinary.config(
    cloud_name='deafb5r6t',
    api_key='524957462776911',
    api_secret='vgoe-i8dYNLyCEbsFaJ4v_sJx-I'
)

user_router = APIRouter(prefix="/users")

class CreateUserRequest(BaseModel):
    username:str = Field(...)
    password_plain:str = Field(...)
    
# this function must send all the processed images in pdf format
@user_router.get("/{user_id}/projects/{project_id}/results")
async def get_results():
    return {"hello": "results"}

# Register User
@user_router.post("/register", response_model=User)
async def create_user(user_request: CreateUserRequest):
    print("Trying User Creation")
    # Check if user already exists
    existing_user = users_collection.find_one({"username": user_request.username})
    if existing_user:
        print("Username already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    # Hash the password
    hashed_password = hash_password(user_request.password_plain)
    
    # Save user to database
    created_user = User(username=user_request.username, password_hash=hashed_password)
    result = users_collection.insert_one(created_user.model_dump(by_alias=True, exclude=["id"]))
    user = users_collection.find_one({"_id":result.inserted_id})
    print("New User Registered")
    print(user)
    return user

# Upload Images (This function must recieve array of images, process them by adding a text of the image's name in the image and save them to a image database)
@user_router.put("/{user_id}/projects/{project_id}")
async def upload_images(project_id:str, images:list[UploadFile] = File(...)):
    try:
        # db.
        print("Received images:", images)
    except HTTPException as e:
        print(f"Error uploading images: {e}")
        return status.HTTP_400_BAD_REQUEST


@user_router.post("/{user_id}/projects")
async def create_project(user_id:str, project : Project = Body(...)):
    try:
        user_oid = ObjectId(user_id)  # Convert string user_id to ObjectId
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") 

    project.id = str(ObjectId())
    project_dict = project.model_dump(by_alias=True)

    # Add the project to the user's projects array
    update_result = users_collection.update_one({"_id": user_oid},{"$push": {"projects": project_dict}})
    
    get_user_from_id(user_id)
    
    return project_dict

@user_router.delete("/{user_id}/projects/{project_id}")
async def delete_project(user_id:str, project_id:str):
    
    try:
        user_oid = ObjectId(user_id)  
        project_oid = ObjectId(project_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    update_result = users_collection.update_one({"_id": user_oid},{"$pull": {"projects": {"_id": project_id}}})
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User or project not found")
    
    # Retrieve the updated user to return
    updated_user = get_user_from_id(user_id)
    
    return updated_user

@user_router.post("/{user_id}/projects/{project_id}")
async def upload_images_to_project(user_id: str, project_id: str, files: list[UploadFile] = File(...)):
    try:
        user_oid = ObjectId(user_id)  # Convert string user_id to ObjectId
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    user = get_user_from_id(user_id)
    if user is None:
        return HTTPException(status_code=404, detail="User not found")
    
    user_dict = user.model_dump(by_alias=True)

    try:
        project = next((proj for proj in user_dict['projects'] if proj['_id'] == project_id), None)
    except:
        print("here is error")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    image_urls = []
    for file in files:
        try:
            result = cloudinary.uploader.upload(file.file)
            image_urls.append(result['secure_url'])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")

    update_result = users_collection.update_one(
        {"_id": user_oid, "projects._id": project_id},
        {"$push": {"projects.$.images": {"$each": image_urls}}}
    )
    
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Retrieve the updated user to return
    updated_user = get_user_from_id(user_id)
    
    return updated_user