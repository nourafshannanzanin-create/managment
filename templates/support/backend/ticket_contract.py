from dataclasses import dataclass, field
from typing import List


@dataclass
class TicketMessageContract:
    id: int
    sender_name: str
    sender_role: str
    body: str
    is_internal: bool
    created_at: str


@dataclass
class TicketAttachmentContract:
    id: int
    original_name: str
    file_url: str


@dataclass
class TicketDetailContract:
    id: int
    subject: str
    message: str
    category: str
    priority: str
    status: str
    tenant_name: str
    messages: List[TicketMessageContract] = field(default_factory=list)
    attachments: List[TicketAttachmentContract] = field(default_factory=list)
