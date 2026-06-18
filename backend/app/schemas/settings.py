from pydantic import BaseModel


class SettingCard(BaseModel):
    title: str
    description: str
