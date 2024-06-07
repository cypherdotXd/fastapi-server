from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field
from typing import Annotated, Any, Optional

from models.image import Image

PyObjectId = Annotated[str, BeforeValidator(str)]

class Project(BaseModel):
    id:Optional[PyObjectId] = Field(alias="_id", default=ObjectId)
    name:str = Field(...)
    # description:Optional[str] = Field()
    # createdAt:str = 
    images:list[Image] = []
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }