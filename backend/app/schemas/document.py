from pydantic import BaseModel


class ApprovalListItem(BaseModel):
    id: str
    title: str
    owner: str
    type: str
    status: str
    department: str
    uploadedAt: str
    risk: str
    summary: str
