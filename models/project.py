from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field
from typing import Annotated, Any, Optional

PyObjectId = Annotated[str, BeforeValidator(str)]

class Project(BaseModel):
    id:Optional[PyObjectId] = Field(alias="_id", default=ObjectId)
    name:str = Field(...)
    images:Optional[list[str]] = []
    results:Optional[list[Any]] = []
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }