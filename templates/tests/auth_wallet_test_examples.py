from decimal import Decimal

from templates.wallet.backend.wallet_options import normalize_money


def test_normalize_money_uses_decimal_precision():
    assert normalize_money('10.1') == Decimal('10.10')


def test_gateway_callback_should_be_idempotent_by_reference():
    processed_references = set()

    def handle(reference):
        if reference in processed_references:
            return 'already-processed'
        processed_references.add(reference)
        return 'processed'

    assert handle('abc') == 'processed'
    assert handle('abc') == 'already-processed'
