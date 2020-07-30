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
import utils
import config as cfg
import urllib
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
import aiohttp


class StatEmoji(object):
    def __init__(self, how_long, cmd_keys=["stat"]):
        self.cmd_keys = cmd_keys

        self.reset_cache()

        self.loading_flag = False
        self.last_execute_time = 1e999
        self.reset_cache_interval = 30 * 60
        self.how_long = how_long

        self.description = '\n'.join([
            '統計並視覺化字詞/表符於此伺服器的使用頻率，需先使用 collect 指令收集資料後方可使用其他指令',
            '- collect',
            f'  收集近 {self.how_long} 天的所有訊息',
            '',
            '- count_emoji',
            '  統計所有伺服器表符的使用次數',
            '',
            '- hist <text>/<emoji> [<user>]',
            '  繪製 <text>/<emoji> 每日使用次數的直方圖，給定 <user> 會同時顯示 <user> 的每日使用次數',
            '',
            '- pie <user>',
            '  繪製 <user> 使用伺服器表符的次數圓餅圖，<user> 可為 @(tag) 、 伺服器暱稱或帳號名稱',
        ])

    def reset_cache(self):
        self.emoji_dict = {}
        self.messages = []
        self.emoji_image_dict = {}
        self.timestamp = None
        self.current_guild = None

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            args[0] = args[0].lower()
            if self.loading_flag:
                await message.channel.send("Don't use stat command during collecting")

            elif len(args) == 1 and args[0] == "collect":
                await self.run_collect(message)

            elif self.current_guild != message.channel.guild:
                await message.channel.send("Please collect data first")

            elif len(args) == 1 and args[0] == "count_emoji":
                await self.run_count_emoji(message)

            elif len(args) >= 2 and args[0] == "hist":
                await self.run_hist(message, args)

            elif len(args) == 2 and args[0] == "pie":
                await self.run_pie(message, args)

            elif len(args) == 1 and args[0] == "count_msg":
                if self.messages:
                    l = len([msg for msg in self.messages if msg.channel == message.channel])
                    await message.channel.send(content=str(l))

            self.last_execute_time = time.time()
            return True
        return False

    async def run_hist(self, message, args):
        if self.messages:
            timestamps = [m.created_at.timestamp() for m in self.messages if args[1] in m.content]
            mpl_data = mdates.epoch2num(timestamps)
            fig, ax = plt.subplots(1, 1)
            min_date = mdates.epoch2num(self.timestamp - self.how_long * 24 * 60 * 60)
            max_date = mdates.epoch2num(self.timestamp)
            ax.hist(
                mpl_data,
                bins=self.how_long,
                range = (min_date, max_date),
                color='lightblue'
            )
            if len(args) == 3:
                user = utils.get_user_by_name(args[2], message.channel.guild)
                if user:
                    a_timestamps = [
                        m.created_at.timestamp() for m in self.messages if args[1] in m.content and m.author == user
                    ]
                    a_mpl_data = mdates.epoch2num(a_timestamps)
                    ax.hist(a_mpl_data, bins=self.how_long, range = (min_date, max_date), color='lightcoral')

            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            d_file = discord.File(filename="unknown.png", fp=buf)
            await message.channel.send(file=d_file)

    async def run_count_emoji(self, message):
        if self.messages:
            img_emoji_dict, gif_emoji_dict = self.count_all_emojis()
            img_emoji_len_list = [(k, len(v)) for k, v in img_emoji_dict.items()]
            gif_emoji_len_list = [(k, len(v)) for k, v in gif_emoji_dict.items()]

            img_emoji_len_list.sort(key=lambda x: x[1], reverse=True)
            gif_emoji_len_list.sort(key=lambda x: x[1], reverse=True)

            iter_num = math.ceil(len(img_emoji_len_list) / 30)
            emoji_len_list = ["%s: %d" % (k, v) for (k, v) in img_emoji_len_list]
            for i in range(iter_num):
                s = "Image Emoji\n" if i == 0 else ""

                s += ", ".join(emoji_len_list[:30])
                await message.channel.send(s)
                emoji_len_list = emoji_len_list[30:]

            iter_num = math.ceil(len(gif_emoji_len_list) / 30)
            emoji_len_list = ["%s: %d" % (k, v) for (k, v) in gif_emoji_len_list]
            for i in range(iter_num):
                s = "\nGIF Emoji\n" if i == 0 else ""
                s += ", ".join(emoji_len_list[:30])
                await message.channel.send(s)
                emoji_len_list = emoji_len_list[30:]

    def imscatter(self, x, y, image_bytes, ax=None, zoom=1):

        if ax is None:
            ax = plt.gca()
        image = plt.imread(io.BytesIO(image_bytes))
        im = OffsetImage(image, zoom=zoom)
        x, y = np.atleast_1d(x, y)
        artists = []
        for x0, y0 in zip(x, y):
            ab = AnnotationBbox(im, (x0, y0), xycoords='data', frameon=False)
            artists.append(ax.add_artist(ab))
        ax.update_datalim(np.column_stack([x, y]))
        ax.autoscale()
        return artists

    def simplify_pie_data(self, labels, values, threshold=0.05):
        sum_values = sum(values)
        sum_other_values = sum(i for i in values if i / sum_values < threshold)
        labels = [labels[i] for i in range(len(labels)) if values[i] / sum_values >= threshold]
        values = [i for i in values if i / sum_values >= 0.05]
        if sum_other_values > 0:
            labels.append("Others")
            values.append(sum_other_values)
        return labels, values


    async def get_emoji_image_dict(self):
        emojis = self.messages[0].channel.guild.emojis
        emoji_str_list = ["<:%s:%d>" % (e.name, e.id) for e in emojis]
        emoji_image_list = await asyncio.gather(*[utils.get_data_by_url(e.url) for e in emojis])
        emoji_image_dict = {k: v for k, v in zip(emoji_str_list, emoji_image_list)}

        return emoji_image_dict

    async def run_pie(self, message, args):
        user = utils.get_user_by_name(args[1], message.channel.guild)
        if not user:
            await message.channel.send("No Data.")
            return

        if self.messages:
            img_emoji_dict, gif_emoji_dict = self.count_all_emojis(user)
            img_emoji_len_list = [(k, len(v)) for k, v in img_emoji_dict.items()]
            img_emoji_len_list.sort(key=lambda x: x[1], reverse=True)

            labels, values = list(zip(*img_emoji_len_list))
            sum_values = sum(values)
            if sum_values == 0:
                await message.channel.send("No Data.")
                return
            labels, values = self.simplify_pie_data(labels, values)

            fig, ax = plt.subplots(1, 1)
            count_labels = ["%.2f%%\n(%d)" % (v / sum_values * 100, v) for v in values]
            texts = ax.pie(values, labels=labels, labeldistance=0.8, wedgeprops=dict(edgecolor='w'))[1]
            ax.pie(values, labels=count_labels, labeldistance=1.2, wedgeprops=dict(edgecolor='w', alpha=0), textprops=dict(ha="center"))[1]

            if not self.emoji_image_dict:
                self.emoji_image_dict = await self.get_emoji_image_dict()

            for t, l in zip(texts, labels):
                x, y = t.get_position()
                if l in self.emoji_image_dict:
                    t.set_alpha(0)
                    self.imscatter([x], [y], self.emoji_image_dict[l], ax, 0.2)

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            d_file = discord.File(filename="unknown.png", fp=buf)
            await message.channel.send(file=d_file)




    def count_all_emojis(self, user=None):
        img_emoji_dict = {}
        gif_emoji_dict = {}
        emojis = self.messages[0].channel.guild.emojis
        for emoji in emojis:
            str_emoji = ("<a:%s:%d>" if emoji.animated else "<:%s:%d>") % (emoji.name, emoji.id)
            emoji_dict = gif_emoji_dict if emoji.animated else img_emoji_dict
            emoji_dict[str_emoji] = []
            if not user:
                emoji_dict[str_emoji] = [msg for msg in self.messages if str_emoji in msg.content]
            else:
                emoji_dict[str_emoji] = [msg for msg in self.messages if str_emoji in msg.content and user == msg.author]
        return img_emoji_dict, gif_emoji_dict

    async def run_collect(self, message):
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

    async def collect_channel(self, channel):
        emojis = channel.guild.emojis
        emoji_dict = {}
        after_date = datetime.datetime.now().astimezone(pytz.utc) - datetime.timedelta(days=self.how_long)
        after_date = after_date.replace(tzinfo=None)

        try:
            messages = await channel.history(after=after_date, limit=None).flatten()
            messages = [m for m in messages if not m.author.bot and not m.content.startswith(cfg.CMD_PREFIX)]
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
