from decimal import Decimal


def normalize_money(value):
    return Decimal(str(value or 0)).quantize(Decimal('0.01'))


def build_feature_option_payload(config, purchase=None):
    total_amount = normalize_money(config['base_price'])
    paid_amount = normalize_money(getattr(purchase, 'paid_amount', 0))
    remaining_amount = normalize_money(getattr(purchase, 'remaining_amount', 0))
    return {
        'feature_key': config['feature_key'],
        'title': config['title'],
        'subtitle': config.get('subtitle', ''),
        'description': config.get('description', ''),
        'accent': config.get('accent', '#315f9f'),
        'is_active': bool(getattr(purchase, 'is_active', False)),
        'payment_plan': getattr(purchase, 'payment_plan', ''),
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'remaining_amount': remaining_amount,
        'cash_amount': total_amount,
        'monthly_installment_amount': normalize_money(config.get('monthly_installment_amount', 0)),
        'installment_months': int(config.get('installment_months', 0) or 0),
        'next_installment_due_at': getattr(purchase, 'next_installment_due_at', None),
    }


def ledger_entry_payload(*, direction, amount, description, reference_type, reference_id=None):
    return {
        'direction': direction,
        'amount': normalize_money(amount),
        'description': description,
        'reference_type': reference_type,
        'reference_id': reference_id,
    }
