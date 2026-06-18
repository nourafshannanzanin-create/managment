from pydantic import BaseModel


class RequestListItem(BaseModel):
    id: str
    title: str
    owner: str
    manager: str
    priority: str
    status: str
    department: str
    deadline: str
    description: str


class RequestTimelineItem(BaseModel):
    step: int
    title: str
    note: str


class RequestDetailResponse(BaseModel):
    request: RequestListItem
    timeline: list[RequestTimelineItem]
