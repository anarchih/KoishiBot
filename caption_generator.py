
import discord

from PIL import Image
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import io
import numpy as np


def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result

def get_center(x, y, w, h):
    return x - w / 2, (y - h / 2) - h * 0.1

def get_font_by_size_searching(draw, text, _min, _max, width, height):
    for size in range(_min, _max + 2):
        font = ImageFont.truetype("fonts/NotoSansCJK-Regular.ttc", size, encoding="unic")
        w, h = draw.textsize(text, font=font)
        if w > width or h > height:
            break
    if size == _min:
        return None

    font = ImageFont.truetype("fonts/NotoSansCJK-Regular.ttc", size - 1, encoding="unic")
    return font


class BaseCaption(object):
    def __init__(self, cmd_keys=["caption"]):
        self.cmd_keys = cmd_keys
        self.margin_top_w, self.margin_top_b = 0, 0
        self.margin_right_w, self.margin_right_b = 0, 0
        self.margin_bottom_w, self.margin_bottom_b = 0, 0
        self.margin_left_w, self.margin_left_b = 0, 0

        self.margin_color = (0, 0, 0, 255)
        self.text_align = "center"
        self.text_color = (255, 255, 255, 255)
        self.text_width_w, self.text_width_b = 1, 0
        self.text_height_w, self.text_height_b = 1, 0
        self.text_min_size, self.text_max_size = 8, 36
        self.text_x_w, self.text_x_b = .5, 0
        self.text_y_w, self.text_y_b = .5, 0
        self.text_spacing = 0

    def get_image(self, arg, message):
        return Image.new("RGBA", (100, 100), "black")
        draw.text()

    def add_margin(self, img):
        W, H = img.size
        img = add_margin(
            img,
            self.margin_top_w * H + self.margin_top_b,
            self.margin_right_w * W + self.margin_right_b,
            self.margin_bottom_w * H + self.margin_bottom_b,
            self.margin_left_w * W + self.margin_left_b,
            self.margin_color
        )
        return img

    def get_font(self, img, draw, text):
        message = ""
        W, H = img.size
        font = get_font_by_size_searching(
            draw,
            text,
            self.text_min_size,
            self.text_max_size,
            self.text_width_w * W + self.text_width_b,
            self.text_height_w * H + self.text_height_b
        )
        if not font:
            message = "Too many lines or too many characters in one line."
        return font, message

    def set_font(self, img, draw, text, font):
        W, H = img.size
        w, h = draw.textsize(text, font=font)
        x, y = get_center(
            self.text_x_w * W + self.text_x_b,
            self.text_y_w * H + self.text_y_b,
            w,
            h
        )
        draw.multiline_text(
            (x, y),
            text,
            self.text_color,
            font=font,
            align=self.text_align,
            spacing = self.text_spacing
        )

    async def send_image(self, img, channel):
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByteArr = io.BytesIO(imgByteArr.getvalue())
        d_file = discord.File(filename="unknown.png", fp=imgByteArr)
        await channel.send(file=d_file)

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                text = args[0].replace("\\n", "\n")
                img = self.get_image(args[0], message)
                img = self.add_margin(img)
                draw = ImageDraw.Draw(img)

                font, error_message = self.get_font(img, draw, text)
                if error_message:
                    await message.channel.send(error_message)
                    return True

                self.set_font(img, draw, text, font)
                await self.send_image(img, message.channel)
            return True
        return False


