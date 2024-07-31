from pydantic import BaseModel

class ImageSchema(BaseModel):
    img_source: str
    position_x: int
    position_y: int
