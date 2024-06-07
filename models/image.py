from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field
from typing import Annotated, Any, Optional


class Image(BaseModel):
    name:str = Field(...)
    url:Optional[str]
    is_processed:bool = False
    processed_url:Optional[str]
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
        }