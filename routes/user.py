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
    return user

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
    
    get_user_model_from_db(user_id)
    
    return project_dict

@user_router.get("/{user_id}/projects")
async def get_all_projects(user_id:str):
    user = get_user_model_from_db(user_id)
    if user:
        return user.projects
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
@user_router.get("/{user_id}/projects/{project_id}")
async def get_project_of_user(user_id:str, project_id:str):
    user = get_user_model_from_db(user_id)
    if user:
        project = next((proj for proj in user.projects if proj.id == project_id), None)
        if project:
            return project
        else:
            return HTTPException(status_code=404, detail="Project not found")
    else:
        raise HTTPException(status_code=404, detail="User not found")

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
    updated_user = get_user_model_from_db(user_id)
    
    return updated_user

@user_router.post("/{user_id}/projects/{project_id}")
async def upload_images_to_project(user_id: str, project_id: str, images: list[UploadFile] = File(...)):
    try:
        user_oid = ObjectId(user_id)  # Convert string user_id to ObjectId
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    user = get_user_model_from_db(user_id)
    if user is None:
        return HTTPException(status_code=404, detail="User not found")
    

    try:
        project = next((proj for proj in user.projects if proj.id == project_id), None)
    except:
        print("project not found")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    image_urls = []
    for file in images:
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
    updated_user = get_user_model_from_db(user_id)
    if updated_user is None:
        return HTTPException(status_code=404, detail="User not found")
    print(updated_user)
    project = next((proj for proj in updated_user.projects if proj.id == project_id), None)
    print(project)
    return project

@user_router.delete("/{user_id}/projects/{project_id}")
async def delete_all_images(user_id:str, project_id:str):
    try:
        user_oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail = "Invaild user id format")
    
    user = get_user_model_from_db(user_id)
    if user is None:
        return HTTPException(status_code=404, detail="User not found")
    
    user_dict = user.model_dump(by_alias=True)

    try:
        project = next((proj for proj in user_dict['projects'] if proj['_id'] == project_id), None)
    except:
        print("project not found")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update the specific project to clear images
    update_result = users_collection.update_one(
        {"_id": user_id, "projects.id": project_id},
        {"$set": {"projects.$.images": []}}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Retrieve the updated user to return
    get_user_model_from_db(user_id)
    
    return project

@user_router.delete("/{user_id}/projects/{project_id}/{index}")
async def delete_image_in_project(user_id:str, project_id:str, index:int):
    try:
        user_oid = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail = "Invaild user id format")
    
    user = get_user_model_from_db(user_id)
    if user is None:
        return HTTPException(status_code=404, detail="User not found")
    
    user_dict = user.model_dump(by_alias=True)
    # print(user.projects[0].id == project_id)
    
    try:
        project = next((proj for proj in user.projects if proj.id == project_id), None)
    except:
        print("project not found")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if the image index is within bounds
    if index < 0 or project.images and index >= len(project.images):
        raise HTTPException(status_code=400, detail="Invalid image index")

    if project.images: del project.images[index]


    # Update the specific project to clear images
    result = users_collection.update_one(
        {"_id": user_oid, "projects._id": project_id},
        {"$set": {"projects.$.images": project.images}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project couldn't be updated")
    
    if project.images:
        print(len(project.images))

    return project