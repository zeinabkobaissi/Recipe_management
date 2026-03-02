from sqlalchemy import create_engine, Column, Integer, String, Text
from database import Base



class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    cuisine_type = Column(String(50), nullable=False)
    preparation_time = Column(Integer, nullable=True)  # in minutes
    serving_size = Column(Integer, nullable=True)  # number of servings