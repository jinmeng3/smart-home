from pydantic import BaseModel, Field


class ExecuteSceneInput(BaseModel):
    scene_id: str = Field(min_length=1, max_length=64)
