from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from workflow.live import record_live_event
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


def _emit(instance, event_type: str, data: dict, *, tenant_id: int | None, actor_user_id: int | None = None) -> None:
    """Write a small, scoped invalidation in the same DB transaction.

    Model signals run during ``save()``; ``record_live_event`` delays fanout
    until ``transaction.on_commit`` so rollback cannot reach a browser.
    """
    entity_type = event_type.split(".", 1)[0]
    action = "created" if event_type.endswith(".created") else "updated"
    record_live_event(
        event_type,
        data,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=getattr(instance, "code", None) or instance.pk,
        action=action,
        actor_user_id=actor_user_id,
        version=str(getattr(instance, "updated_at", "") or ""),
    )


@receiver(post_save, sender=Request)
def publish_request_event(sender, instance: Request, created: bool, **kwargs) -> None:
    organization_id = _request_organization_id(instance)
    _emit(
        instance,
        "request.created" if created else "request.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "user_id": instance.requester_id,
            "code": instance.code,
            "status": instance.status,
            "request_type": instance.request_type,
        },
        tenant_id=organization_id,
        actor_user_id=instance.requester_id,
    )


@receiver(post_save, sender=Expense)
def publish_expense_event(sender, instance: Expense, created: bool, **kwargs) -> None:
    organization_id = _owned_organization_id(instance)
    _emit(
        instance,
        "expense.created" if created else "expense.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "user_id": instance.owner_id,
            "code": instance.code,
            "status": instance.status,
            "category": instance.category,
        },
        tenant_id=organization_id,
        actor_user_id=instance.owner_id,
    )


@receiver(post_save, sender=Document)
def publish_document_event(sender, instance: Document, created: bool, **kwargs) -> None:
    organization_id = _owned_organization_id(instance)
    _emit(
        instance,
        "document.created" if created else "document.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "user_id": instance.owner_id,
            "code": instance.code,
            "status": instance.status,
        },
        tenant_id=organization_id,
        actor_user_id=instance.owner_id,
    )


@receiver(post_save, sender=SupportTicket)
def publish_support_ticket_event(sender, instance: SupportTicket, created: bool, **kwargs) -> None:
    organization_id = getattr(instance, "organization_id", None)
    _emit(
        instance,
        "support.ticket.created" if created else "support.ticket.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "status": instance.status,
            "priority": instance.priority,
        },
        tenant_id=organization_id,
    )


@receiver(post_save, sender=SupportMessage)
def publish_support_message_event(sender, instance: SupportMessage, created: bool, **kwargs) -> None:
    organization_id = instance.ticket.organization_id
    _emit(
        instance,
        "support.message.created" if created else "support.message.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "ticket_id": instance.ticket_id,
            "user_id": instance.sender_id,
        },
        tenant_id=organization_id,
        actor_user_id=instance.sender_id,
    )


@receiver(post_save, sender=DirectMessage)
def publish_chat_message_event(sender, instance: DirectMessage, created: bool, **kwargs) -> None:
    organization_id = instance.conversation.organization_id
    _emit(
        instance,
        "chat.message.created" if created else "chat.message.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "conversation_id": instance.conversation_id,
            "sender_id": instance.sender_id,
            "user_ids": list(instance.conversation.memberships.values_list("user_id", flat=True)),
        },
        tenant_id=organization_id,
        actor_user_id=instance.sender_id,
    )


@receiver(post_save, sender=Task)
def publish_task_event(sender, instance: Task, created: bool, **kwargs) -> None:
    organization_id = instance.organization_id
    _emit(
        instance,
        "task.created" if created else "task.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "code": instance.code,
            "status": instance.status,
        },
        tenant_id=organization_id,
        actor_user_id=instance.creator_id,
    )


@receiver(post_save, sender=TaskComment)
def publish_task_comment_event(sender, instance: TaskComment, created: bool, **kwargs) -> None:
    organization_id = instance.task.organization_id
    _emit(
        instance,
        "task.comment.created" if created else "task.comment.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "task_id": instance.task_id,
            "user_id": instance.author_id,
        },
        tenant_id=organization_id,
        actor_user_id=instance.author_id,
    )


@receiver(post_save, sender=AttendanceEvent)
def publish_attendance_event(sender, instance: AttendanceEvent, created: bool, **kwargs) -> None:
    organization_id = _user_organization_id(instance.user)
    _emit(
        instance,
        "attendance.created" if created else "attendance.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "user_id": instance.user_id,
            "event_type": instance.event_type,
        },
        tenant_id=organization_id,
        actor_user_id=instance.user_id,
    )


@receiver(post_save, sender=WalletTransaction)
def publish_wallet_event(sender, instance: WalletTransaction, created: bool, **kwargs) -> None:
    organization_id = instance.wallet.organization_id
    _emit(
        instance,
        "wallet.transaction.created" if created else "wallet.transaction.updated",
        {
            **_base_payload(instance, created),
            "organization_id": organization_id,
            "wallet_id": instance.wallet_id,
            "transaction_type": instance.transaction_type,
        },
        tenant_id=organization_id,
    )
