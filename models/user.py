from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Annotated, Optional, Union

from models.project import *


class User(BaseModel):
    # id:Optional[PyObjectId] = Field(alias="_id", default=None)
    username:str = Field(...)
    password_hash:str = Field(...)
    projects:Optional[list[Project]] = []
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }

