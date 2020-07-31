
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
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from utils import get_data_by_url, is_url
import pickle
import os
import time
from PIL import Image
import math


class Sentiment(object):
    def __init__(self, cmd_keys=["sentiment"]):
        self.cmd_keys = cmd_keys
        self.client = language.LanguageServiceClient()
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

        self.description = '\n'.join([
            "文本情感分析",
            "- <text>",
            "  分析文本 <text> 屬於正面或負面情感",
        ])

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            cur_month = datetime.now(tz=timezone.utc).month
            if time.time() - self.last_execute_time < self.cool_down:
                await message.channel.send("Please wait for %d seconds." % (self.cool_down + self.last_execute_time - time.time()))
                return

            if self.usage[0] != cur_month:
                self.usage = [cur_month, 0]
            if self.usage[1] < 5000:
                text = ".".join(args)
                document = types.Document(
                    content=text,
                    type=enums.Document.Type.PLAIN_TEXT
                )
                sentiment = self.client.analyze_sentiment(document=document).document_sentiment
                print(sentiment.score, sentiment.magnitude)
                if sentiment.score > 0.1 and sentiment.magnitude > 0.2:
                    await message.channel.send(":)")
                elif sentiment.score < -0.1 and sentiment.magnitude > 0.2:
                    await message.channel.send(":(")
                else:
                    await message.channel.send("??")

                self.usage[1] += math.ceil(len(text) / 1000)
                with open(self.usage_file_path, "wb") as f:
                    pickle.dump(self.usage, f)

                # await message.channel.send(s)

            return True
        else:
            return False

