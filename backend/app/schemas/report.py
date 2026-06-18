from pydantic import BaseModel


class ReportCard(BaseModel):
    title: str
    description: str
    export: str
