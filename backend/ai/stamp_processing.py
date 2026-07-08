from __future__ import annotations

import base64
import io

from PIL import Image, ImageChops, ImageFilter


def decode_image_data_url(data_url: str) -> Image.Image:
    if "," not in data_url:
        raise ValueError("فرمت تصویر مهر معتبر نیست.")
    _, encoded = data_url.split(",", 1)
    try:
        binary = base64.b64decode(encoded)
    except Exception as exc:
        raise ValueError("خواندن تصویر مهر انجام نشد.") from exc
    return Image.open(io.BytesIO(binary)).convert("RGBA")


def encode_image_data_url(image: Image.Image) -> str:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    encoded = base64.b64encode(stream.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def remove_white_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    difference = ImageChops.difference(rgba, background)
    grayscale = difference.convert("L")
    alpha = grayscale.point(lambda value: 0 if value < 18 else min(255, int(value * 2.6)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=0.8))
    cleaned = rgba.copy()
    cleaned.putalpha(alpha)
    return cleaned


def normalize_stamp_data_url(data_url: str) -> str:
    image = decode_image_data_url(data_url)
    processed = remove_white_background(image)
    return encode_image_data_url(processed)
