import math


def render_sms_text(template_text, recipient, tenant_name=''):
    text = str(template_text or '').strip()
    replacements = {
        '[نام مشتری]': recipient.get('name', '') or 'مشتری',
        '[نام کارواش]': recipient.get('carwash_name', '') or tenant_name or 'کارواش',
        '[تعداد سفارش]': str(recipient.get('orders_count', 0) or 0),
        '[جمع خرید]': str(recipient.get('total_spent', 0) or 0),
        '[امتیاز]': str(recipient.get('score', 0) or 0),
        '[پلاک]': recipient.get('primary_plate', '') or '',
    }
    for token, value in replacements.items():
        text = text.replace(token, str(value))
    return text


def sms_segments(text, segment_size=70):
    normalized = str(text or '').strip()
    if not normalized:
        return 0
    return max(1, math.ceil(len(normalized) / segment_size))


def group_recipients_by_rendered_text(recipients, template_text, tenant_name=''):
    grouped = {}
    for recipient in recipients:
        rendered = render_sms_text(template_text, recipient, tenant_name=tenant_name)
        grouped.setdefault(rendered, []).append({**recipient, 'rendered_text': rendered})
    return grouped
