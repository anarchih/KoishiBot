import discord
import random
import pickle
import datetime as dt
from datetime import datetime
import bisect
import os
import aiohttp
import io
import re

class AlarmClockEvent(object):
    def __init__(self, minute, comments, channel_ids):
        self.minute = minute
        self.comments = comments
        self.channel_ids = channel_ids

class DailyAlarmClock(object):
    def __init__(self, cmd_keys=["clock"], event_path="clock_event.pickle"):
        self.cmd_keys = cmd_keys
        self.event_path = event_path
        self.init_done = False

        self.load_file()
        self.init_executed_list()

    def load_file(self):
        if os.path.isfile(self.event_path):
            with open(self.event_path, "rb") as f:
                self.event_dict = pickle.load(f)
        else:
            self.event_dict = {}

    def save_file(self):
        with open(self.event_path, "wb") as f:
            pickle.dump(self.event_dict, f)

    def init_executed_list(self):
        self.pointer_dict = {k: -1 for k in self.event_dict}
        cur_time = datetime.now()
        self.today = cur_time.day
        for guild_id in self.event_dict:
            for i, e in enumerate(self.event_dict[guild_id]):
                if cur_time.hour * 60 + cur_time.minute > e.minute:
                    self.pointer_dict[guild_id] = i
            self.pointer_dict[guild_id] += 1
        self.init_done = True

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                sub_cmd = args[0].lower()
                if sub_cmd == "save":
                    await self.save_event(args[1:], message)
                elif sub_cmd == "delete":
                    await self.delete_event(args[1:], message)
                elif sub_cmd == "list":
                    await self.list_event(args[1:], message)
            return True
        else:
            return False


    async def save_event(self, args, message):
        if len(args) >= 2:
            time, comment = args[0], args[1]
            try:
                hour, minute = time.split(":")
                minute = int(minute) + int(hour) * 60
            except:
                await message.channel.send("Error")

            channel = message.channel
            if channel.guild.id not in self.event_dict:
                self.event_dict[channel.guild.id] = []
                self.pointer_dict[channel.guild.id] = 0

            event_list = self.event_dict[channel.guild.id]
            minute_list = [e.minute for e in event_list]
            idx = bisect.bisect_left(minute_list, minute)
            if len(minute_list) > idx and minute_list[idx] == minute:
                event_list[idx].comments.append(comment)
                event_list[idx].channel_ids.append(channel.id)
            else:
                event_list.insert(idx, AlarmClockEvent(minute, [comment], [channel.id]))
                if self.pointer_dict[channel.guild.id] > idx:
                    self.pointer_dict[channel.guild.id] += 1
                elif self.pointer_dict[channel.guild.id] == idx:
                    cur_time = datetime.now()
                    cur_minute = cur_time.minute + cur_time.hour * 60
                    if cur_minute > minute:
                        self.pointer_dict[channel.guild.id] += 1

            self.save_file()
            await message.channel.send("Successfully Saved")
        else:
            await message.channel.send("Error")

    async def list_event(self, args, message):
        channel = message.channel
        if channel.guild.id in self.event_dict:
            display_list = [e.minute for e in self.event_dict[channel.guild.id]]
            display_list = [str(m // 60).zfill(2) + ":" + str(m % 60).zfill(2) for m in display_list]
            s = "Existing Times:\n- "
            s += "\n- ".join(display_list)
            if channel:
                return await channel.send(content=s)
            else:
                return None

        else:
            await channel.send("Error")

    async def delete_event(self, args, message):
        channel = message.channel
        if channel.guild.id in self.event_dict:
            try:
                hour, minute = args[0].split(":")
                minute = int(minute) + int(hour) * 60
            except:
                await message.channel.send("Error")

            for i, event in enumerate(self.event_dict[channel.guild.id]):
                if event.minute == minute:
                    self.event_dict[channel.guild.id].remove(event)
                    if self.pointer_dict[channel.guild.id] > i:
                        self.pointer_dict[channel.guild.id] -= 1
                    await channel.send("Successfully Deleted")
                    break
        else:
            await channel.send("Guild Error")

    def change_day(self, cur_time):
        self.today = cur_time.day
        for guild_id in self.event_dict:
            self.pointer_dict[guild_id] = 0

    async def on_time(self, client):
        if not self.init_done:
            return

        cur_time = datetime.now()
        if self.today != cur_time.day:
            self.change_day(cur_time)

        cur_minute = cur_time.minute + cur_time.hour * 60
        for guild_id in self.event_dict:
            if self.pointer_dict[guild_id] >= len(self.event_dict[guild_id]):
                continue

            pointer = self.pointer_dict[guild_id]
            event = self.event_dict[guild_id][pointer]

            if event.minute <= cur_minute:
                channel = client.get_channel(event.channel_ids[0])
                await channel.send(event.comments[0])
                self.pointer_dict[guild_id] += 1


class History(object):
    def __init__(self, cmd_keys=["history"]):
        self.cmd_keys = cmd_keys


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            channel = message.channel
            if args:
                target_channel = None
                channels = channel.guild.channels
                for c in channels:
                    if args[0] == c.name and isinstance(c, discord.TextChannel):
                        target_channel = c
                        break
                if not target_channel:
                    await channel.send("Can't find the channel.")
                    return True
            else:
                target_channel = channel

            first_message = await target_channel.history(limit=1, oldest_first=True).flatten()
            last_message = await target_channel.history(limit=1, oldest_first=False).flatten()

            start_time = first_message[0].created_at
            end_time = last_message[0].created_at
            while True:
                r = random.randrange(0, int((end_time - start_time).total_seconds()))
                date = start_time + dt.timedelta(seconds=r)
                msg_list = await target_channel.history(around=date).flatten()
                if msg_list:
                    msg = random.choice(msg_list)
                    link = "https://discordapp.com/channels/%d/%d/%d\n" % (target_channel.guild.id, target_channel.id, msg.id)
                    link += msg.author.display_name + " : \n"
                    link += "> " + msg.content.replace("\n", "\n > ") + "\n"
                    if not msg.embeds:
                        await channel.send(link)
                    else:
                        await channel.send(link, embed=msg.embeds[0])
                        for e in msg.embeds[1:]:
                            await channel.send(embed=e)
                    break
            return True
        else:
            return False

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

class EmojiRaw(object):
    def __init__(self, cmd_keys=["er"]):
        self.cmd_keys = cmd_keys

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                emojis = re.findall(r"<:.+:([0-9]+)>", args[0])
                if emojis:
                    url = "https://cdn.discordapp.com/emojis/%s.png" % emojis[0]
                    print(url)
                    image = await self.get_image_by_url(url)
                    buf = io.BytesIO(image)
                    buf.seek(0)
                    d_file = discord.File(filename="unknown.png", fp=buf)
                    await message.channel.send(file=d_file)

                emojis = re.findall(r"<a:.+:([0-9]+)>", args[0])
                if emojis:
                    url = "https://cdn.discordapp.com/emojis/%s.gif" % emojis[0]
                    print(url)
                    image = await get_data_by_url(url)
                    buf = io.BytesIO(image)
                    buf.seek(0)
                    d_file = discord.File(filename="unknown.gif", fp=buf)
                    await message.channel.send(file=d_file)
            return True
        return False

    async def get_image_by_url(self, url):
        async with aiohttp.ClientSession() as client:
            async with client.get(str(url)) as res:
                return await res.read()

class GuildReactionEcho(object):
    def __init__(self):
        pass

    async def on_message(self, message):
        emojis = message.channel.guild.emojis
        for emoji in emojis:
            if str(emoji) in message.content:
                await message.add_reaction(emoji)

