from pydantic import BaseModel

class Recipe(BaseModel):
    id: int
    title: str
    ingredients: str
    instructions: str
    status:str
    cuisine_type:str
    preparation_time: int = None  # in minutes
    serving_size: int = None  # number of servings