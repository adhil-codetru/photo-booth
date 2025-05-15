from pydantic import BaseModel , Field , field_validator
from typing import Literal
import re
from better_profanity import profanity

profanity.load_censor_words()
CATEGORIES = Literal[
    "portrait", "landscape", "wildlife", "architecture", "food", 
    "sports", "fashion", "travel", "macro", "abstract"
]

class ClassificationResult(BaseModel):
    category : CATEGORIES

class DescriptionResult(BaseModel):
    description : str = Field(...,max_length=200)

    @field_validator("description")
    @classmethod
    def sensor_profanity(cls,v):
        if profanity.contains_profanity(v):
            raise ValueError("Decription contains profanity")
        return v.strip()