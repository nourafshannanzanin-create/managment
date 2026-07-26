from templates.sms.backend.sms_templates import group_recipients_by_rendered_text, sms_segments


def test_sms_segments_counts_minimum_one_segment():
    assert sms_segments('hello') == 1


def test_group_recipients_batches_equal_rendered_texts():
    recipients = [
        {'name': 'Ali', 'carwash_name': 'A'},
        {'name': 'Ali', 'carwash_name': 'A'},
        {'name': 'Sara', 'carwash_name': 'A'},
    ]
    grouped = group_recipients_by_rendered_text(recipients, 'سلام [نام مشتری]', tenant_name='A')
    assert len(grouped) == 2
