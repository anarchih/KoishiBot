from utils import get_data_by_url
from PIL import Image
import io
import random
import numpy as np
import discord


class ImageProcessing(object):
    def __init__(self, cmd_keys=["image"]):
        self.cmd_keys = cmd_keys
        self.description = '\n'.join([
            '影像處理工具',
            '- color_inverse',
            '  對上傳的圖片做負片處理',
            '',
            '- channel_swap',
            '  隨機置換上傳圖片的 RGB Channel',
        ])


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1 and args[0] == "channel_swap":
                await self.run_channel_swap(message)
            elif len(args) == 1 and args[0] == "color_inverse":
                await self.run_color_inverse(message)
            return True
        else:
            return False

    async def get_images_by_message(self, message):
        attachment = message.attachments[0]
        images = []
        for attachment in message.attachments:
            url, filename_ext = attachment.url, attachment.filename
            img_bytes = await get_data_by_url(url)
            try:
                images.append(Image.open(io.BytesIO(img_bytes)))
            except OSError:
                pass
        return images

    async def run_color_inverse(self, message):
        images = await self.get_images_by_message(message)
        attachments = []
        for img in images:
            img_arr = np.array(img)

            if len(img_arr.shape) < 3:
                continue
            for i in range(min(3, img_arr.shape[2])):
                img_arr[:, :, i] = 255 - img_arr[:, :, i]

            with io.BytesIO() as f:
                Image.fromarray(img_arr).save(f, 'png')
                byte = f.getvalue()
                buf = io.BytesIO(byte)
                buf.seek(0)
                d_file = discord.File(filename="unknown.png", fp=buf)

                attachments.append(d_file)
        await message.channel.send(files=attachments)

    async def run_channel_swap(self, message):
        images = await self.get_images_by_message(message)
        attachments = []
        for img in images:
            img_arr = np.array(img)
            if len(img_arr.shape) < 3 or img_arr.shape[2] < 3:
                continue
            r = random.sample([0, 1, 2], 3)
            r = r if img_arr.shape[2] == 3 else r + [3]

            with io.BytesIO(

            ) as f:
                Image.fromarray(img_arr[:, :, r]).save(f, 'png')
                byte = f.getvalue()
                buf = io.BytesIO(byte)
                buf.seek(0)
                d_file = discord.File(filename="unknown.png", fp=buf)

                attachments.append(d_file)
        await message.channel.send(files=attachments)



