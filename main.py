"""
WEB sayt Skrinshot Dasturi

O'rnatish:
    pip install playwright Pillow
    python -m playwright install chromium

Ishga tushirish:
    python certificate_screenshot.py
"""

from playwright.sync_api import sync_playwright
from PIL import Image
import os

LINKS = [
    "https://www.hackerrank.com/certificates/iframe/a4c4c09c5ec0",
    "https://www.hackerrank.com/certificates/iframe/72a2c3cbe4ff",
    "https://www.hackerrank.com/certificates/iframe/4c322c21d960",
    "https://www.hackerrank.com/certificates/iframe/08f10e27fc2d",
    "https://www.hackerrank.com/certificates/iframe/277bf2393e4b",
]


OUTPUT_FOLDER = "screenshots"


def crop_certificate(temp_path, out_path):
    """
    To'liq sahifa screenshotidan faqat sertifikat kartasini kesib oladi.
    Header (qora) va footer (oq)ni o'tkazib, sertifikat chegara chizig'ini topadi.
    Sertifikat: och kulrang border bilan o'ralgan oq karta.
    """
    img = Image.open(temp_path).convert("RGB")
    w, h = img.size
    pixels = img.load()

    # --- 1. HEADER BALANDLIGINI TOPISH ---
    # Header qora (#1a1a1a yoki #2b2b2b), oq fon boshlanishi = header tugadi
    header_end = 0
    for y in range(h):
        # O'rtadagi pikselli tekshirish
        r, g, b = pixels[w // 2, y]
        # Oq yoki juda och fon (header tugadi)
        if r > 230 and g > 230 and b > 230:
            header_end = y
            break

    # --- 2. FOOTER BOSHLANISHINI TOPISH ---
    # Footer: eng pastdagi qora bo'lmagan qism
    footer_start = h
    for y in range(h - 1, header_end, -1):
        r, g, b = pixels[w // 2, y]
        if r > 230 and g > 230 and b > 230:
            footer_start = y
        else:
            break

    # --- 3. SERTIFIKAT KARTASINI TOPISH ---
    # header_end dan footer_start oralig'ida sertifikat bor
    # Sertifikat border: kulrang (~200 qiymati), atrofi esa to'liq oq (255)
    # Chapdan o'ngga: sertifikat boshlangan joyni topish
    search_y = (header_end + footer_start) // 2  # O'rta qator

    left_x = w // 4
    for x in range(w // 10, w // 2):
        r, g, b = pixels[x, search_y]
        if r < 240 or g < 240 or b < 240:
            left_x = x
            break

    right_x = 3 * w // 4
    for x in range(w - w // 10, w // 2, -1):
        r, g, b = pixels[x, search_y]
        if r < 240 or g < 240 or b < 240:
            right_x = x
            break

    # Yuqori chegara (header_end dan pastga)
    top_y = header_end
    for y in range(header_end, footer_start):
        r, g, b = pixels[w // 2, y]
        if r < 240 or g < 240 or b < 240:
            top_y = y
            break

    # Quyi chegara
    bot_y = footer_start
    for y in range(footer_start, header_end, -1):
        r, g, b = pixels[w // 2, y]
        if r < 240 or g < 240 or b < 240:
            bot_y = y
            break

    pad = 8
    box = (
        max(0, left_x - pad),
        max(0, top_y - pad),
        min(w, right_x + pad),
        min(h, bot_y + pad),
    )

    print(f"        Crop box: {box}, img size: {w}x{h}")
    cropped = img.crop(box)
    cropped.save(out_path, "PNG")
    return cropped.size


def take_screenshot(page, url, index, total):
    print(f"[{index:02d}/{total}] {url}")
    try:
        page.goto(url, wait_until="networkidle", timeout=40000)
        page.wait_for_timeout(3000)

        # Cookie OK tugmasini bosish
        try:
            ok_btn = page.locator("button:has-text('OK')").first
            if ok_btn.is_visible(timeout=2000):
                ok_btn.click()
                page.wait_for_timeout(600)
        except:
            pass

        temp_file = os.path.join(OUTPUT_FOLDER, f"_tmp_{index:02d}.png")
        out_file  = os.path.join(OUTPUT_FOLDER, f"certificate_{index:02d}.png")

        # Viewport screenshot (full_page=False - header bor lekin Pillow keser)
        page.screenshot(path=temp_file, full_page=False)

        cw, ch = crop_certificate(temp_file, out_file)
        if os.path.exists(temp_file):
            os.remove(temp_file)

        print(f"        ✓ Saqlandi ({cw}x{ch}): {out_file}")
        return out_file

    except Exception as e:
        print(f"        ✗ Xato: {e}")
        return None


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    total = len(LINKS)
    print(f"\n{total} ta sertifikat screenshot olinmoqda...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        results = []
        for i, url in enumerate(LINKS, start=1):
            result = take_screenshot(page, url, i, total)
            results.append(result)

        context.close()
        browser.close()

    success = sum(1 for r in results if r)
    print(f"\nTugadi! {success}/{total} ta screenshot saqlandi.")
    print(f"Papka: ./{OUTPUT_FOLDER}/")


if __name__ == "__main__":
    main()
