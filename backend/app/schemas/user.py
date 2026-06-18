from pydantic import BaseModel


class UserListItem(BaseModel):
    name: str
    role: str
    department: str
    kpi: str
