import discord
import random
import pickle
import datetime as dt
from datetime import datetime, timezone
import bisect
import os
import aiohttp
import io
import re
from google.cloud import vision
from google.cloud.vision import types
from utils import get_image_by_url, is_url
import pickle
import os
import time
from PIL import Image


class ImageLabel(object):
    def __init__(self, cmd_keys=["label"]):
        self.cmd_keys = cmd_keys
        self.client = vision.ImageAnnotatorClient()
        self.cool_down = 60 * 3
        self.last_execute_time = 0
        self.usage_file_path = "visionai.pickle"
        if os.path.exists(self.usage_file_path):
            with open(self.usage_file_path, "rb") as f:
                self.usage = pickle.load(f)
        else:
            self.usage = [datetime.now(tz=timezone.utc).month, 0]
            with open(self.usage_file_path, "wb") as f:
                pickle.dump(self.usage, f)

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            cur_month = datetime.now(tz=timezone.utc).month
            if time.time() - self.last_execute_time < self.cool_down:
                await message.channel.send("Please wait for %d seconds." % (self.cool_down + self.last_execute_time - time.time()))
                return

            if self.usage[0] != cur_month:
                self.usage = [cur_month, 0]
            if self.usage[1] < 1000:
                if message.attachments:
                    url = message.attachments[0].url
                elif len(args) >= 1 and is_url(args[0]):
                    url = args[0]
                else:
                    await message.channel.send("Please input the image url or upload the image.")
                    return

                data = await get_image_by_url(url)
                try:
                    Image.open(io.BytesIO(data))
                except OSError:
                    await message.channel.send("Illegal file format")
                    return

                image = types.Image(content=data)
                response = self.client.label_detection(image=image)
                labels = response.label_annotations
                s = "\n"
                for label in labels:
                    s += "%s: %f\n" % (label.description, label.score)

                self.usage[1] += 1
                with open(self.usage_file_path, "wb") as f:
                    pickle.dump(self.usage, f)

                await message.channel.send(s)

            return True
        else:
            return False

