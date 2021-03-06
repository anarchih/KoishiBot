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
from utils import get_data_by_url


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
        self.description = '\n'.join([
            '- [<channel_name>]',
            '  從 <channel_name> 或當前 channel 的歷史紀錄中隨機挑選一條訊息',
        ])

    def get_target_channel(self, args, channel):
        if args:
            target_channel = None
            channels = channel.guild.channels
            for c in channels:
                if args[0] == c.name and isinstance(c, discord.TextChannel):
                    target_channel = c
                    break
            if not target_channel:
                return None
        else:
            target_channel = channel

        return target_channel

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            channel = message.channel
            target_channel = get_target_channel(args, channel)
            if not target_channel:
                await channel.send("Can't find the channel.")
                return

            target_time = get_target_time(args, target_channel)
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
                    if msg.mentions:
                        await channel.send(link)
                        break
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
        self.description = '\n'.join([
            '- <item1> [<item2> ...]',
            '  從 <item1> ... <itemX> 中隨機選擇一個',
        ])


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
        self.description = '\n'.join([
            '- <custom_emoji>',
            '  顯示 <custom_emoji> 的原圖',
        ])

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                emojis = re.findall(r"<:.+:([0-9]+)>", args[0])
                if emojis:
                    url = "https://cdn.discordapp.com/emojis/%s.png" % emojis[0]
                    print(url)
                    image = await get_data_by_url(url)
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


class GuildReactionEcho(object):
    def __init__(self):
        pass

    async def on_message(self, message):
        emojis = message.channel.guild.emojis
        for emoji in emojis:
            if str(emoji) in message.content:
                await message.add_reaction(emoji)


class EmojiArt(object):
    def __init__(self, path, cmd_keys=["emoji_art"]):
        self.cmd_keys = cmd_keys
        self.emojiart_dict_path = path
        self.nil_emoji_str = "<:nil:735852429391953920>"

        self.list_keywords = ["list", "ls", "l"]
        self.save_keywords = ["save", "sv", "s"]
        self.delete_keywords = ["delete", "del", "d"]
        self.rename_keywords = ["rename", "rn"]
        self.keywords = sum([
            self.list_keywords,
            self.save_keywords,
            self.delete_keywords,
            self.rename_keywords
        ], [])

    def load_emojiart_dict(self):
        try:
            with open(self.emojiart_dict_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            with open(self.emojiart_dict_path, "wb") as f:
                pickle.dump({}, f)
                return {}


    def save_emojiart_dict(self, emojiart_dict):
        with open(self.emojiart_dict_path, "wb") as f:
            pickle.dump(emojiart_dict, f)

    def get_args_in_code_block(self, text, startsfrom=0):
        text = text[startsfrom:]
        cb_symbols = list(re.finditer("```", text))
        if len(cb_symbols) < 2:
            return []

        start, end = cb_symbols[0].span()[1], cb_symbols[-1].span()[0]
        return shlex.split(text[start: end])

    def get_symbol_table(self, emojis, args):
        symbol_set = set("".join(args)) - {"."}
        if len(symbol_set) > len(emojis):
            return {}

        emojis = random.sample(emojis, len(symbol_set))
        z = {}
        for i, c in enumerate(symbol_set):
            emoji_str = '<a:%s:%d>' if emojis[i].animated else '<:%s:%d>'
            emoji_str = emoji_str % (emojis[i].name, emojis[i].id)
            z[c] = emoji_str

        return z

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if args:
                if args[0] in self.save_keywords:
                    await self.run_save(args, message)
                elif args[0] in self.list_keywords:
                    await self.run_list(args, message)
                elif args[0] in self.delete_keywords:
                    await self.run_delete(args, message)
                elif args[0] in self.rename_keywords:
                    await self.run_rename(args, message)
                else:
                    await self.run_display(args, message)
            return True
        return False

    async def run_list(self, args, message):
        emojiart_dict = self.load_emojiart_dict()
        self.emojiart_list = [k for k in emojiart_dict.keys()]
        s = "Existing Files:\n- "
        s += "\n- ".join(self.emojiart_list[0:20])
        await message.channel.send(s)
        return True

    async def run_delete(self, args, message):
        if len(args) >= 2:
            emojiart_dict = self.load_emojiart_dict()
            if args[1] in emojiart_dict:
                del emojiart_dict[args[1]]
                self.save_emojiart_dict(emojiart_dict)
                await message.channel.send("Successfully Deleted")
                return True
        await message.channel.send("Unable to find the keyword or arguments are not enough.")
        return False

    async def run_rename(self, args, message):
        if len(args) >= 3:
            emojiart_dict = self.load_emojiart_dict()
            if args[1] in emojiart_dict:
                emojiart_dict[args[2]] = emojiart_dict[args[1]]
                del emojiart_dict[args[1]]
                self.save_emojiart_dict(emojiart_dict)
                await message.channel.send("Successfully Renamed")
                return True
        await message.channel.send("Unable to find the keyword or arguments are not enough.")
        return False

    async def run_save(self, args, message):
        if len(args) >= 3:
            if args[1] in self.keywords:
                await message.channel.send("Failed to Save: Do not use the keywords.")
                return False
            if message.mentions:
                await message.channel.send("Don't mention anyone in file save command")
                return False

            emojiart_dict = self.load_emojiart_dict()
            idx = message.content.find(args[1])
            text = message.content[idx + len(args[1]):]
            if len(list(re.finditer("```", text))) >= 2:
                emojiart_dict[args[1]] = text
                self.save_emojiart_dict(emojiart_dict)
                await message.channel.send("Successfully Saved")
                return True

        await message.channel.send("Illegal Arguments")
        return False

    async def run_display(self, args, message):
        if len(args) >= 1:
            emojiart_dict = self.load_emojiart_dict()
            text = emojiart_dict[args[0]] if args[0] in emojiart_dict else message.content
            cb_args = self.get_args_in_code_block(text)
            if not cb_args:
                await message.channel.send("Unable to find the code block")
                return True

            symbol_table = self.get_symbol_table(message.channel.guild.emojis, cb_args)
            if not symbol_table:
                await message.channel.send("Too many symbols")
                return True

            s_list = []
            for arg in cb_args:
                s = ""
                for i, c in enumerate(arg[::-1]):
                    if c != ".":
                        break
                i = None if i == 0 else -i
                for c in arg[:i]:
                    if c == ".":
                        s += self.nil_emoji_str
                        continue
                    else:
                        s += symbol_table[c]
                s_list.append(s)
            try:
                s = "\n".join(s_list)
                if s:
                    await message.channel.send(s)
            except discord.errors.HTTPException:
                await message.channel.send("String Length > 2000")

        return True


class Help(object):
    def __init__(self, agent, cmd_keys=["help"]):
        self.cmd_keys = cmd_keys
        self.agent = agent
        self.description = '\n'.join([
            '- [<command_name>]'
            '  顯示全部指令或指令名為 <command_name> 的說明文件',
        ])

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            # s = "指令型功能\n"
            s = ""
            for app in self.agent.event_dict["on_command"]:
                if args and args[0] not in app.cmd_keys:
                    continue

                s += "=== " + "/".join(app.cmd_keys) + " ===\n"
                try:
                    s += "\t" + app.description.replace("\n", "\n\t") + "\n\n"
                except:
                    s += "\t" + "No Document\n\n"
            if s:
                await message.channel.send("```\n" + s + "```")
            return True
        else:
            return False

