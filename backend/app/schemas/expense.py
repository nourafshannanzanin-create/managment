from pydantic import BaseModel


class ExpenseSummaryItem(BaseModel):
    label: str
    value: str


class ExpenseListItem(BaseModel):
    id: str
    title: str
    amount: str
    category: str
    owner: str
    status: str
    progress: int
