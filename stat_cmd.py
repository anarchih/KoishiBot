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
    def __init__(self, how_long, cmd_keys=["stat"]):
        self.cmd_keys = cmd_keys

        self.reset_cache()

        self.loading_flag = False
        self.last_execute_time = 1e999
        self.reset_cache_interval = 20 * 60
        self.how_long = how_long

    def reset_cache(self):
        self.emoji_dict = {}
        self.messages = []
        self.timestamp = None
        self.current_guild = None

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            args[0] = args[0].lower()
            if self.loading_flag:
                await message.channel.send("Don't use stat command while collecting")

            elif len(args) == 1 and args[0] == "collect":
                self.loading_flag = True
                await message.channel.send("Start collecting")
                self.reset_cache()
                channels = message.channel.guild.channels
                self.timestamp = time.time()
                done, _ = await asyncio.wait(
                    [self.collect_channel(ch) for ch in channels if ch.type == discord.ChannelType.text]
                )
                self.messages = sum([f.result() for f in done], [])
                await message.channel.send("Finished")
                self.current_guild = message.channel.guild
                self.loading_flag = False

            elif self.current_guild != message.channel.guild:
                await message.channel.send("Please collect data first")

            elif len(args) == 1 and args[0] == "count_emoji":
                if self.messages:
                    emoji_dict = self.count_all_emojis()
                    emoji_len_list = [(k, len(v)) for k, v in self.emoji_dict.items()]
                    emoji_len_list.sort(key=lambda x: x[1], reverse=True)
                    iter_num = math.ceil(len(emoji_len_list) / 30)
                    emoji_len_list = ["%s: %d" % (k, v) for (k, v) in emoji_len_list]
                    for i in range(iter_num):
                        s = ", ".join(emoji_len_list[:30])
                        await message.channel.send(s)
                        emoji_len_list = emoji_len_list[30:]
            elif len(args) == 2 and args[0] == "hist":
                if self.messages and args[1]:
                    timestamps = [m.created_at.timestamp() for m in self.messages if args[1] in m.content]
                    mpl_data = mdates.epoch2num(timestamps)
                    fig, ax = plt.subplots(1, 1)
                    min_date = mdates.epoch2num(self.timestamp - self.how_long * 24 * 60 * 60)
                    max_date = mdates.epoch2num(self.timestamp)
                    ax.hist(mpl_data, bins=self.how_long, range = (min_date, max_date), color='lightblue')
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                    plt.xticks(rotation=45)
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    d_file = discord.File(filename="unknown.png", fp=buf)
                    await message.channel.send(file=d_file)
            elif len(args) == 1 and args[0] == "count_msg":
                if self.messages:
                    l = len([msg for msg in self.messages if msg.channel == message.channel])
                    await message.channel.send(content=str(l))



            self.last_execute_time = time.time()
            return True
        return False

    def count_all_emojis(self):
        if self.emoji_dict:
            return self.emoji_dict
        emoji_dict = {}
        emojis = self.messages[0].channel.guild.emojis
        for emoji in emojis:
            str_emoji = (("<a" if emoji.animated else "<") + ":%s:%d>") % (emoji.name, emoji.id)
            emoji_dict[str_emoji] = [msg for msg in self.messages if str_emoji in msg.content]
            # [msg.created_at for msg in message if str_emoji in msg.reactions]
        self.emoji_dict = emoji_dict
        return emoji_dict

    async def collect_channel(self, channel):
        emojis = channel.guild.emojis
        emoji_dict = {}
        after_date = datetime.datetime.now().astimezone(pytz.utc) - datetime.timedelta(days=self.how_long)
        after_date = after_date.replace(tzinfo=None)

        try:
            messages = await channel.history(after=after_date, limit=None).flatten()
            messages = [m for m in messages if not m.author.bot]
            print(channel, len(messages))
        except discord.errors.Forbidden:
            messages = []
        return messages


    def combine_dict(self, list_of_dict):
        new_dict = {}
        if len(list_of_dict) == 0:
            return new_dict
        for emoji in list_of_dict[0]:
            new_dict[emoji] = sum([d[emoji] for d in list_of_dict], [])
            new_dict[emoji].sort(key=lambda x: x.created_at)
        return new_dict

    async def on_time(self, client):
        if time.time() - self.last_execute_time > self.reset_cache_interval:
            self.last_execute_time = 1e999
            self.reset_cache()
