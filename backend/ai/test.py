import cv2
import numpy as np
from PIL import Image


def remove_white_background(input_path, output_path):
    # خواندن تصویر
    img = cv2.imread(input_path)

    if img is None:
        raise Exception("تصویر پیدا نشد!")

    # تبدیل به RGBA
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # تبدیل به HSV برای تشخیص بهتر سفیدی
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # محدوده رنگ سفید
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 80, 255])

    # ماسک قسمت‌های سفید
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    # کمی نرم کردن ماسک برای لبه‌های طبیعی
    kernel = np.ones((3,3), np.uint8)
    white_mask = cv2.morphologyEx(
        white_mask,
        cv2.MORPH_OPEN,
        kernel
    )

    # تبدیل سفیدها به شفافیت
    alpha = 255 - white_mask

    # نرم کردن لبه‌ها
    alpha = cv2.GaussianBlur(
        alpha,
        (3,3),
        0
    )

    # قرار دادن آلفا روی تصویر
    img_rgba[:,:,3] = alpha

    # ذخیره PNG شفاف
    result = Image.fromarray(
        cv2.cvtColor(img_rgba, cv2.COLOR_BGRA2RGBA)
    )

    result.save(
        output_path,
        "PNG"
    )

    print("انجام شد:", output_path)


# استفاده:
remove_white_background(
    "Stamp-nut-and-bolt-store_40186.jpg",
    "stamp_no_background.png"
)

remove_white_background(
    "ggg.jpg",
    "stamp_no__background.png"
)