from sqlmodel import SQLModel, Field
from typing import Optional

class Favorite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    wine_name: str
    wine_link: str
    image_url: str
    rating: float
    price: float
    region: str
    country: str



