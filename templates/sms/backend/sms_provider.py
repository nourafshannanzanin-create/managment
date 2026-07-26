import json
from dataclasses import dataclass
from urllib import error as urllib_error
from urllib import request as urllib_request


@dataclass(frozen=True)
class SmsProviderRequest:
    text: str
    recipients: list[str]


class SmsProvider:
    def send_single(self, payload: SmsProviderRequest):
        raise NotImplementedError


class HttpSmsProvider(SmsProvider):
    def __init__(self, *, base_url, api_key, line_number):
        self.base_url = str(base_url).rstrip('/')
        self.api_key = str(api_key).strip()
        self.line_number = str(line_number).strip()

    def send_single(self, payload: SmsProviderRequest):
        body = {
            'text': payload.text,
            'line_number': self.line_number,
            'recipients': payload.recipients,
            'number_format': 'english',
            'schedule': None,
        }
        req = urllib_request.Request(
            url=f'{self.base_url}/ws/v1/sms/simple',
            data=json.dumps(body).encode('utf-8'),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Api-Key': self.api_key,
            },
            method='POST',
        )
        try:
            with urllib_request.urlopen(req, timeout=15) as response:
                raw_body = response.read().decode('utf-8')
                return {
                    'ok': response.status in {200, 201},
                    'status_code': response.status,
                    'raw_body': raw_body,
                }
        except urllib_error.HTTPError as exc:
            return {
                'ok': False,
                'status_code': exc.code,
                'raw_body': exc.read().decode('utf-8', errors='replace'),
            }
