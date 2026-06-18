from pydantic import BaseModel

from app.schemas.document import ApprovalListItem
from app.schemas.expense import ExpenseListItem, ExpenseSummaryItem
from app.schemas.report import ReportCard
from app.schemas.request import RequestListItem
from app.schemas.settings import SettingCard
from app.schemas.user import UserListItem


class StatCard(BaseModel):
    id: str
    label: str
    value: str
    detail: str
    tone: str
    icon: str


class ChartPoint(BaseModel):
    day: str
    value: int


class PipelineItem(BaseModel):
    label: str
    count: int


class ActivityItem(BaseModel):
    id: int
    user: str
    action: str
    detail: str
    time: str
    icon: str


class ApprovalMetrics(BaseModel):
    pending: int
    approved: int
    rejected: int


class BootstrapResponse(BaseModel):
    currentUser: dict
    stats: list[StatCard]
    chartData: list[ChartPoint]
    pipeline: list[PipelineItem]
    requests: list[RequestListItem]
    expenses: list[ExpenseListItem]
    approvals: list[ApprovalListItem]
    users: list[UserListItem]
    reports: list[ReportCard]
    activities: list[ActivityItem]
    insights: list[str]
    expenseSummary: list[ExpenseSummaryItem]
    approvalMetrics: ApprovalMetrics
    settingsCards: list[SettingCard]
