import discord
import datetime
import asyncio
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
import io
import time
import math


class StatEmoji(object):
    def __init__(self, cmd_keys=["stat"]):
        self.cmd_keys = cmd_keys
        self.emoji_dict = {}
        self.timestamp = None
        self.loading_flag = False
        self.how_long = 7 * 4

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            args[0] = args[0].lower()
            if self.loading_flag:
                await message.channel.send("Don't use stat command while loading")

            elif len(args) == 1 and args[0] == "load":
                self.loading_flag = True
                await message.channel.send("Start Loading")
                channels = message.channel.guild.channels
                self.timestamp = time.time()
                done, _ = await asyncio.wait(
                    [self.stat_channel(ch) for ch in channels if ch.type == discord.ChannelType.text]
                )
                list_of_dict = [f.result() for f in done]
                self.emoji_dict = self.combine_dict(list_of_dict)
                await message.channel.send("Finished")
                self.loading_flag = False
            elif len(args) == 1 and args[0] == "count_all":
                if self.emoji_dict:
                    emoji_len_list = [(k, len(v)) for k, v in self.emoji_dict.items()]
                    emoji_len_list.sort(key=lambda x: x[1], reverse=True)
                    iter_num = math.ceil(len(emoji_len_list) / 30)
                    emoji_len_list = ["%s: %d" % (k, v) for (k, v) in emoji_len_list]
                    for i in range(iter_num):
                        s = ", ".join(emoji_len_list[:30])
                        await message.channel.send(s)
                        emoji_len_list = emoji_len_list[30:]
            elif len(args) == 2 and args[0] == "hist":
                if self.emoji_dict and args[1] in self.emoji_dict:
                    timestamps = [m.created_at.timestamp() for m in self.emoji_dict[args[1]]]
                    mpl_data = mdates.epoch2num(timestamps)
                    fig, ax = plt.subplots(1, 1)
                    min_date = mdates.epoch2num(self.timestamp - self.how_long * 24 * 60 * 60)
                    max_date = mdates.epoch2num(self.timestamp)
                    ax.hist(mpl_data, bins=self.how_long, range = (min_date, max_date), color='lightblue')
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    d_file = discord.File(filename="unknown.png", fp=buf)
                    await message.channel.send(file=d_file)

            return True
        return False

    async def stat_channel(self, channel):
        emojis = channel.guild.emojis
        emoji_dict = {}
        after_date = datetime.datetime.now().astimezone(pytz.utc) - datetime.timedelta(days=self.how_long)
        after_date = after_date.replace(tzinfo=None)
        try:
            messages = await channel.history(after=after_date, limit=None).flatten()
        except discord.errors.Forbidden:
            messages = []

        for emoji in emojis:
            str_emoji = (("<a" if emoji.animated else "<") + ":%s:%d>") % (emoji.name, emoji.id)
            emoji_dict[str_emoji] = [msg for msg in messages if str_emoji in msg.content]
            # [msg.created_at for msg in message if str_emoji in msg.reactions]
        return emoji_dict

    def combine_dict(self, list_of_dict):
        new_dict = {}
        if len(list_of_dict) == 0:
            return new_dict
        for emoji in list_of_dict[0]:
            new_dict[emoji] = sum([d[emoji] for d in list_of_dict], [])
            new_dict[emoji].sort(key=lambda x: x.created_at)
        return new_dict
