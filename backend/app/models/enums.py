from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EXECUTIVE_MANAGER = "executive_manager"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class RequestPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ExpenseStatus(StrEnum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    NEEDS_DOCUMENT = "needs_document"
    REJECTED = "rejected"


class ExpenseCategory(StrEnum):
    SALARY = "salary"
    EQUIPMENT = "equipment"
    MARKETING = "marketing"
    TRANSPORTATION = "transportation"
    MAINTENANCE = "maintenance"
    OFFICE_SUPPLIES = "office_supplies"
    MISCELLANEOUS = "miscellaneous"
    TECHNOLOGY = "technology"
    OPERATIONS = "operations"
    CAPITAL = "capital"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    WAITING_SIGNATURE = "waiting_signature"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DocumentRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidentialityLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    STRICT = "strict"
