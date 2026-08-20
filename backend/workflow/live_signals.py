from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from workflow.live import publish_live_event
from workflow.models import (
    AttendanceEvent,
    DirectMessage,
    Document,
    Expense,
    Request,
    SupportMessage,
    SupportTicket,
    Task,
    TaskComment,
    WalletTransaction,
)


def _base_payload(instance, created: bool) -> dict:
    payload = {
        "id": instance.pk,
        "created": created,
    }
    organization_id = getattr(instance, "organization_id", None)
    if organization_id:
        payload["organization_id"] = organization_id
    return payload


def _user_organization_id(user) -> int | None:
    membership = getattr(user, "organization_membership", None)
    return getattr(membership, "organization_id", None)


def _request_organization_id(instance: Request) -> int | None:
    return _user_organization_id(getattr(instance, "requester", None))


def _owned_organization_id(instance) -> int | None:
    return _user_organization_id(getattr(instance, "owner", None))


@receiver(post_save, sender=Request)
def publish_request_event(sender, instance: Request, created: bool, **kwargs) -> None:
    publish_live_event(
        "request.created" if created else "request.updated",
        {
            **_base_payload(instance, created),
            "organization_id": _request_organization_id(instance),
            "user_id": instance.requester_id,
            "code": instance.code,
            "status": instance.status,
            "request_type": instance.request_type,
        },
    )


@receiver(post_save, sender=Expense)
def publish_expense_event(sender, instance: Expense, created: bool, **kwargs) -> None:
    publish_live_event(
        "expense.created" if created else "expense.updated",
        {
            **_base_payload(instance, created),
            "organization_id": _owned_organization_id(instance),
            "user_id": instance.owner_id,
            "code": instance.code,
            "status": instance.status,
            "category": instance.category,
        },
    )


@receiver(post_save, sender=Document)
def publish_document_event(sender, instance: Document, created: bool, **kwargs) -> None:
    publish_live_event(
        "document.created" if created else "document.updated",
        {
            **_base_payload(instance, created),
            "organization_id": _owned_organization_id(instance),
            "user_id": instance.owner_id,
            "code": instance.code,
            "status": instance.status,
        },
    )


@receiver(post_save, sender=SupportTicket)
def publish_support_ticket_event(sender, instance: SupportTicket, created: bool, **kwargs) -> None:
    publish_live_event(
        "support.ticket.created" if created else "support.ticket.updated",
        {
            **_base_payload(instance, created),
            "status": instance.status,
            "priority": instance.priority,
        },
    )


@receiver(post_save, sender=SupportMessage)
def publish_support_message_event(sender, instance: SupportMessage, created: bool, **kwargs) -> None:
    publish_live_event(
        "support.message.created" if created else "support.message.updated",
        {
            **_base_payload(instance, created),
            "organization_id": instance.ticket.organization_id,
            "ticket_id": instance.ticket_id,
            "user_id": instance.sender_id,
        },
    )


@receiver(post_save, sender=DirectMessage)
def publish_chat_message_event(sender, instance: DirectMessage, created: bool, **kwargs) -> None:
    publish_live_event(
        "chat.message.created" if created else "chat.message.updated",
        {
            **_base_payload(instance, created),
            "organization_id": instance.conversation.organization_id,
            "conversation_id": instance.conversation_id,
            "sender_id": instance.sender_id,
            "user_ids": list(instance.conversation.memberships.values_list("user_id", flat=True)),
        },
    )


@receiver(post_save, sender=Task)
def publish_task_event(sender, instance: Task, created: bool, **kwargs) -> None:
    publish_live_event(
        "task.created" if created else "task.updated",
        {
            **_base_payload(instance, created),
            "code": instance.code,
            "status": instance.status,
        },
    )


@receiver(post_save, sender=TaskComment)
def publish_task_comment_event(sender, instance: TaskComment, created: bool, **kwargs) -> None:
    publish_live_event(
        "task.comment.created" if created else "task.comment.updated",
        {
            **_base_payload(instance, created),
            "organization_id": instance.task.organization_id,
            "task_id": instance.task_id,
            "user_id": instance.author_id,
        },
    )


@receiver(post_save, sender=AttendanceEvent)
def publish_attendance_event(sender, instance: AttendanceEvent, created: bool, **kwargs) -> None:
    publish_live_event(
        "attendance.created" if created else "attendance.updated",
        {
            **_base_payload(instance, created),
            "user_id": instance.user_id,
            "event_type": instance.event_type,
        },
    )


@receiver(post_save, sender=WalletTransaction)
def publish_wallet_event(sender, instance: WalletTransaction, created: bool, **kwargs) -> None:
    publish_live_event(
        "wallet.transaction.created" if created else "wallet.transaction.updated",
        {
            **_base_payload(instance, created),
            "wallet_id": instance.wallet_id,
            "transaction_type": instance.transaction_type,
        },
    )
