from dataclasses import dataclass
from decimal import Decimal
import os


@dataclass(frozen=True)
class SmsProviderConfig:
    base_url: str
    api_key: str
    line_number: str
    price_per_segment: Decimal


def load_sms_provider_config(env=None):
    env = env or os.environ
    return SmsProviderConfig(
        base_url=str(env.get('SMS_PROVIDER_BASE_URL', 'https://api.example.com')).rstrip('/'),
        api_key=str(env.get('SMS_PROVIDER_API_KEY', '')).strip(),
        line_number=str(env.get('SMS_PROVIDER_LINE_NUMBER', '')).strip(),
        price_per_segment=Decimal(str(env.get('SMS_PRICE_PER_SEGMENT', '500'))),
    )
