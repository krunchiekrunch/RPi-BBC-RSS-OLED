import time
import requests
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import busio
import json

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

i2c = busio.I2C(board.SCL, board.SDA)
display = adafruit_ssd1306.SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)
display.fill(0)
display.show()

font = ImageFont.load_default()

NEWS_URL = "https://api.rss2json.com/v1/api.json?rss_url=http://feeds.bbci.co.uk/news/rss.xml"

# scrolling settings
SCROLL_DELAY = 0.03  # delay between scroll steps
LINE_SPACING = 1     # extra pixel between lines so it looks better
SCROLL_PIXELS = 1    # scroll 1 pixel at a time

def fetch_news():
    try:
        response = requests.get(NEWS_URL, timeout=5)
        data = response.json()
        articles = [item["title"] + "\n" + item.get("description", "") for item in data.get("items", [])]
        return articles
    except Exception as e:
        print("Error fetching:", e)
        return ["Failed to fetch"]

def wrap_text_pixel(text, font, draw, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip() if line else word
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                if line:
                    lines.append(line)
                # split very long words character by character if doesnt fit
                char_line = ""
                for char in word:
                    test_char_line = char_line + char
                    if draw.textlength(test_char_line, font=font) <= max_width:
                        char_line = test_char_line
                    else:
                        if char_line:
                            lines.append(char_line)
                        char_line = char
                line = char_line
        if line:
            lines.append(line)
    return lines

def show_article(article):
    """Scroll text vertically with pixel-perfect wrapping"""
    # top and bottom of feed
    full_text = "[BBC News]\n\n" + article + "\n[END]\n"

    # measure text width
    temp_img = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT))
    draw = ImageDraw.Draw(temp_img)

    # wrap text to fit width
    lines = wrap_text_pixel(full_text, font, draw, SCREEN_WIDTH)

    # extra blank line at the end for spacing
    lines.append("")

    # calculate line height incl spacing
    line_height = (font.getbbox("A")[3] - font.getbbox("A")[1]) + LINE_SPACING
    img_height = len(lines) * line_height

    # make image for the full text
    img = Image.new("1", (SCREEN_WIDTH, img_height), 0)
    draw_local = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw_local.text((0, i * line_height), line, font=font, fill=255)

    # scroll if feed is taller than screen
    if img_height <= SCREEN_HEIGHT:
        display.image(img.crop((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)))
        display.show()
        time.sleep(3)
    else:
        # scroll so the last pixel of the last line aligns with the bottom
        for y in range(0, img_height - SCREEN_HEIGHT + 1, SCROLL_PIXELS):
            display.image(img.crop((0, y, SCREEN_WIDTH, y + SCREEN_HEIGHT)))
            display.show()
            time.sleep(SCROLL_DELAY)
        time.sleep(1)

if __name__ == "__main__":
    while True:
        articles = fetch_news()
        for article in articles:
            show_article(article)