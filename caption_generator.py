
import discord

from PIL import Image
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import io


class ImageText(object):
    def __init__(self, cmd_keys=["say"]):
        self.cmd_keys = cmd_keys
        self.t_pad, self.r_pad, self.b_pad, self.l_pad = 80, 40, 0, 40
        self.margin_color = (255, 255, 255, 255)
        self.text_width_a, self.text_height_a = .9, .9
        self.text_width_b, self.text_height_b = 0, 0
        # self.typeface_file = typeface_file
        pass
    def set_font(self, img, draw, text):
        return
    def get_image(self, arg, message):
        filename = "annoy.png"
        return Image.open(filename)

    async def on_command(self, cmd, args, message):
        print(cmd)
        if cmd in self.cmd_keys:
            print(args)
            if len(args) >= 2:
                text = args[1].replace("\\n", "\n")
                img = self.get_image(args[0], message)
                img = self.add_margin(img)
                draw = ImageDraw.Draw(img)

                W, H = img.size
                font, w, h  = self.get_font(draw, text, W * .9, self.t_pad * .9)
                if not font:
                    await message.channel.send("Too many lines or too many characters in single line.")
                    return True

                x, y = self.get_center(0, W, self.t_pad, 0, w, h)
                draw.multiline_text((x, y), text, (0, 0, 0, 0,), font=font, align="center")

                await self.send_image(img, message.channel)
            return True
        return False

    def get_font(self, draw, text, width, height):
        for size in range(8, 37):
            font = ImageFont.truetype("NotoSansCJK-Regular.ttc", size, encoding="unic")
            w, h = draw.textsize(text, font=font)
            if w > width or h > height:
                break
        if size == 8:
            return None, w, h

        font = ImageFont.truetype("NotoSansCJK-Regular.ttc", size - 1, encoding="unic")
        w, h = draw.textsize(text, font=font)
        return font, w, h

    def get_center(self, top, right, bottom, left, w, h):
        x = ((right - left) - w) / 2
        y = ((bottom - top) - h) / 2
        return x, y

    async def send_image(self, img, channel):
        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format='PNG')
        imgByteArr = io.BytesIO(imgByteArr.getvalue())
        d_file = discord.File(filename="unknown.png", fp=imgByteArr)
        await channel.send(file=d_file)

    def add_margin(self, pil_img):
        top, right, bottom, left = self.t_pad, self.r_pad, self.b_pad, self.l_pad
        color = self.margin_color

        width, height = pil_img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(pil_img.mode, (new_width, new_height), color)
        result.paste(pil_img, (left, top))
        return result
