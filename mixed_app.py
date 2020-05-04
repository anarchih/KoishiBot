import discord
import random
import pickle
from datetime import datetime
import bisect
import os


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

class MahjongEmojiDisplay(object):
    def __init__(self, cmd_keys=["mahjong", "mj"]):
        self.cmd_keys = cmd_keys
        self.mj_dict = {
            "1m": "<:1m:690877262542667776>",
            "1p": "<:1p:690877262572158987>",
            "1s": "<:1s:690877263125676073>",
            "1z": "<:1z:690877263297773629>",
            "2m": "<:2m:690877263784181762>",
            "2p": "<:2p:690877263947890699>",
            "2z": "<:2z:690877264321183834>",
            "3p": "<:3p:690877264388161549>",
            "2s": "<:2s:690877264438624258>",
            "3m": "<:3m:690877264681893929>",
            "3s": "<:3s:690877264967106680>",
            "5z": "<:5z:690877265751310446>",
            "3z": "<:3z:690877266468798485>",
            "4z": "<:4z:690877267676495972>",
            "4m": "<:4m:690877268179943466>",
            "7z": "<:7z:690877268192657448>",
            "4s": "<:4s:690877268330807330>",
            "6z": "<:6z:690877268561494087>",
            "5s": "<:5s:690877268675002368>",
            "6m": "<:6m:690877268729397318>",
            "7m": "<:7m:690877268775534592>",
            "8m": "<:8m:690877268951564328>",
            "5m": "<:5m:690877269044101182>",
            "7s": "<:7s:690877269409005569>",
            "8p": "<:8p:690877269433909339>",
            "9s": "<:9s:690877269480308768>",
            "9m": "<:9m:690877269488435311>",
            "5p": "<:5p:690877269555806239>",
            "4p": "<:4p:690877269648080986>",
            "0s": "<:0s:690877269710995466>",
            "0m": "<:0m:690877269731966996>",
            "8s": "<:8s:690877269815722014>",
            "6s": "<:6s:690877269824110633>",
            "0p": "<:0p:690877269949808640>",
            "7p": "<:7p:690877269987557379>",
            "6p": "<:6p:690877269991882752>",
            "9p": "<:9p:690877270155329566>",
        }
    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1:
                s = self.resolve_string(args[0])
                if s:
                    await message.channel.send(s)
                else:
                    await message.channel.send("Illegal Input")

            return True
        else:
            return False

    def resolve_string(self, string):
        tiles = []
        tmps = []
        flag = False
        for c in string:
            if "0" <= c <= "9":
                tmps.append(c)
            elif c == "s" or c == "z" or c == "m" or c == "p":
                try:
                    tiles.extend([self.mj_dict[t + c] for t in tmps])
                except:
                    return None
                flag = True
                tmps = []
            else:
                return None
        if not flag:
            return None
        return "".join(tiles)

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

