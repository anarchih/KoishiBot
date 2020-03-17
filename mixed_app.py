import discord
import random
from PIL import Image
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import io


class Choose(object):
    def __init__(self, cmd_keys=["choose"]):
        self.cmd_keys = cmd_keys


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                r = random.randint(0, len(args) - 1)
                await message.channel.send(args[r])
            return True
        else:
            return False


class GuildReactionEcho(object):
    def __init__(self):
        pass

    async def on_message(self, message):
        emojis = message.channel.guild.emojis
        for emoji in emojis:
            if str(emoji) in message.content:
                await message.add_reaction(emoji)

class ImageText(object):
    def __init__(self, cmd_keys=["say"]):
        self.cmd_keys = cmd_keys
        pass

    async def on_command(self, cmd, args, message):
        print(cmd)
        if cmd in self.cmd_keys:
            print(args)
            if len(args) >= 2:
                filename = "happy.png"#args[0]
                text = args[1]

                img = Image.open(filename)
                img = self.add_margin(img, 50, 0, 0, 0, (255, 255, 255, 255))
                W, H = img.size
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("NotoSansCJK-Regular.ttc", 16, encoding="unic")
                w, h = draw.textsize(text, font=font)

                draw.text(((W-w)/2,(50-h)/2), text, (0, 0, 0, 0,), font=font)
                imgByteArr = io.BytesIO()
                img.save(imgByteArr, format='PNG')
                imgByteArr = io.BytesIO(imgByteArr.getvalue())

                d_file = discord.File(filename=filename, fp=imgByteArr)
                await message.channel.send(file=d_file)
                return True
        return False

    def add_margin(self, pil_img, top, right, bottom, left, color):
        width, height = pil_img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(pil_img.mode, (new_width, new_height), color)
        result.paste(pil_img, (left, top))
        return result
