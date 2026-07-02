from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings

from workflow.models import ApprovalAssignment, ApprovalAssignmentStatus, Document

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
PDF_EXTENSIONS = {".pdf"}


def _load_pymupdf():
    try:
        import fitz  # type: ignore

        return fitz
    except ModuleNotFoundError:
        try:
            import pymupdf as fitz  # type: ignore

            return fitz
        except ModuleNotFoundError as exc:
            raise ValueError("کتابخانه PyMuPDF نصب نیست. برای امضای PDF آن را نصب کنید.") from exc


def _load_pillow():
    try:
        from PIL import Image, ImageOps  # type: ignore

        return Image, ImageOps
    except ModuleNotFoundError as exc:
        raise ValueError("کتابخانه Pillow نصب نیست. برای امضای فایل آن را نصب کنید.") from exc


def _document_path(file_name: str) -> Path:
    return Path(settings.MEDIA_ROOT) / file_name


def _signed_file_name(source_path: Path) -> str:
    extension = source_path.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        extension = ".png"
    return f"{source_path.stem}-signed-{uuid4().hex[:8]}{extension}"


def _decode_signature_data(signature_data: str) -> Image.Image:
    Image, _ = _load_pillow()
    if "," not in signature_data:
        raise ValueError("Invalid signature payload.")
    _, encoded = signature_data.split(",", 1)
    binary = base64.b64decode(encoded)
    return Image.open(io.BytesIO(binary)).convert("RGBA")


def _build_signature_overlay(signature_image: Image.Image) -> Image.Image:
    _, ImageOps = _load_pillow()
    grayscale = ImageOps.grayscale(signature_image)
    alpha = grayscale.point(lambda value: 0 if value > 245 else min(255, int((255 - value) * 2.2)))
    Image, _ = _load_pillow()
    overlay = Image.new("RGBA", signature_image.size, (36, 73, 82, 0))
    overlay.putalpha(alpha)
    return overlay


def _approved_slot_index(document: Document, assignment: ApprovalAssignment) -> int:
    approved_ids = list(
        document.approval_assignments.filter(status=ApprovalAssignmentStatus.APPROVED)
        .order_by("acted_at", "id")
        .values_list("id", flat=True)
    )
    return approved_ids.index(assignment.id)


def _signature_target_size(signature_overlay: Image.Image, canvas_width: float, canvas_height: float) -> tuple[int, int]:
    max_width = max(120, int(canvas_width * 0.22))
    max_height = max(44, int(canvas_height * 0.11))
    width, height = signature_overlay.size
    scale = min(max_width / width, max_height / height)
    scaled_width = max(80, int(width * scale))
    scaled_height = max(28, int(height * scale))
    return scaled_width, scaled_height


def sign_document_file(document: Document, assignment: ApprovalAssignment, signature_data: str) -> str:
    if not document.file_name:
        raise ValueError("Document file is missing.")

    source_path = _document_path(document.file_name)
    if not source_path.exists():
        raise FileNotFoundError(f"Document file not found: {source_path}")

    signature_image = _build_signature_overlay(_decode_signature_data(signature_data))
    extension = source_path.suffix.lower()
    slot_index = _approved_slot_index(document, assignment)
    signed_file_name = _signed_file_name(source_path)
    signed_path = _document_path(signed_file_name)

    if extension in IMAGE_EXTENSIONS:
        _sign_image_document(source_path, signed_path, signature_image, slot_index)
    elif extension in PDF_EXTENSIONS:
        _sign_pdf_document(source_path, signed_path, signature_image, slot_index)
    else:
        raise ValueError("Only image and PDF documents can be signed.")

    if source_path != signed_path and source_path.exists():
        try:
            os.remove(source_path)
        except OSError:
            pass
    return signed_file_name


def _sign_image_document(source_path: Path, signed_path: Path, signature_image: Image.Image, slot_index: int) -> None:
    Image, _ = _load_pillow()
    base_image = Image.open(source_path).convert("RGBA")
    target_width, target_height = _signature_target_size(signature_image, base_image.width, base_image.height)
    resized_signature = signature_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

    margin_x = max(20, int(base_image.width * 0.04))
    margin_y = max(18, int(base_image.height * 0.04))
    slot_gap = max(14, int(base_image.width * 0.02))
    x = max(margin_x, base_image.width - margin_x - resized_signature.width - slot_index * (resized_signature.width + slot_gap))
    y = max(margin_y, base_image.height - margin_y - resized_signature.height)

    layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    layer.paste(resized_signature, (x, y), resized_signature)
    composed = Image.alpha_composite(base_image, layer)
    composed.save(signed_path, format="PNG")


def _sign_pdf_document(source_path: Path, signed_path: Path, signature_image: Image.Image, slot_index: int) -> None:
    fitz = _load_pymupdf()
    stream = io.BytesIO()
    signature_image.save(stream, format="PNG")
    signature_bytes = stream.getvalue()

    pdf_document = fitz.open(source_path)
    try:
        page = pdf_document[-1]
        target_width, target_height = _signature_target_size(signature_image, page.rect.width, page.rect.height)
        margin_x = max(22, int(page.rect.width * 0.05))
        margin_y = max(18, int(page.rect.height * 0.05))
        slot_gap = max(12, int(page.rect.width * 0.02))
        x0 = max(margin_x, page.rect.width - margin_x - target_width - slot_index * (target_width + slot_gap))
        y0 = max(margin_y, page.rect.height - margin_y - target_height)
        rect = fitz.Rect(x0, y0, x0 + target_width, y0 + target_height)
        page.insert_image(rect, stream=signature_bytes, keep_proportion=True, overlay=True)
        pdf_document.save(signed_path, garbage=4, deflate=True)
    finally:
        pdf_document.close()
