import pickle
import discord
import time
import os
import random
import unicodedata


class KeywordReply(object):
    def __init__(self, keywords_path, min_time_gap, recover_time, cmd_keys=["keyword"]):
        self.cmd_keys = cmd_keys
        self.keywords_path = keywords_path
        self.min_time_gap = min_time_gap
        self.recover_time = recover_time
        self.prob = 1
        self.max_size = 30
        self.min_keyword_size = 6
        self.max_keyword_size = 100
        self.max_response_size = 200
        self.last_triggered_time = 0
        self.last_recover_time = 0
        self.command_lock = False

        if not os.path.exists(self.keywords_path):
            with open(self.keywords_path, "wb") as f:
                pickle.dump({}, f)

        with open(self.keywords_path, "rb") as f:
            self.keywords = pickle.load(f)

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            args[0] = args[0].lower()
            if len(args) == 3 and args[0] == "save":
                await self.save_keyword(args, message)
            elif len(args) == 2 and args[0] == "delete":
                await self.delete_keyword(args, message)
            elif len(args) == 3 and args[0] == "rename":
                await self.rename_keyword(args, message)
            elif len(args) == 1 and args[0] == "list":
                await self.list_keyword(message)

            return True
        return False

    def save_to_file(self):
        with open(self.keywords_path, "wb") as f:
            pickle.dump(self.keywords, f)

    def calc_size(self, text):
        count = 0
        for c in text:
            _type = unicodedata.east_asian_width(c)
            if _type == "W" or _type == "F" or _type == "A":
                count += 2
            else:
                count += 1
        return count

    async def save_keyword(self, args, message):
        author = message.author
        channel = message.channel
        if len(self.keywords) >= self.max_size:
            await channel.send("Too many keywords")
            return

        key, response = args[1], args[2]
        count = self.calc_size(key)
        if count < self.min_keyword_size or count > self.max_keyword_size:
            await channel.send("Length of keyword is too long/short")
        elif len(response) > self.max_response_size:
            await channel.send("Length of response is too long")
        else:
            self.keywords[key] = (response, 1, 0, str(author), author.id)
            self.save_to_file()
            await channel.send("Successfully Saved")

    async def delete_keyword(self, args, message):
        channel = message.channel
        key = args[1]
        if key in self.keywords:
            del self.keywords[key]
            self.save_to_file()
            await channel.send("Successfully Deleted")
        else:
            await channel.send("Failed to Delete: {} is not in the list".format(key))

    async def rename_keyword(self, args, message):
        channel = message.channel
        author = message.author
        old_key, new_key = args[1], args[2]

        count = self.calc_size(new_key)
        if count < self.min_keyword_size or count > self.max_keyword_size:
            await channel.send("Length of keyword is too long/short")

        elif old_key in self.keywords:
            data = self.keywords[old_key]
            del self.keywords[old_key]
            self.keywords[new_key] = (*data[0:3], str(author), author.id)
            self.save_to_file()
            await channel.send("Successfully Renamed")
        else:
            await channel.send("Failed to Rename: {} is not in the list".format(old_key))

    async def list_keyword(self, message):
        channel = message.channel
        display_list = list(self.keywords)
        s = "Existing Keywords:\n- "
        s += "\n- ".join(display_list)
        if channel:
            return await channel.send(content=s)
        else:
            return None

    async def on_message(self, message):
        cur_time = time.time()
        diff_time = cur_time - self.last_triggered_time
        if diff_time < self.min_time_gap:
            return

        diff_time = cur_time - self.last_recover_time
        if diff_time > self.recover_time:
            times = int(diff_time / self.recover_time)
            self.prob *= 2 ** times
            self.last_recover_time += times * self.recover_time
            self.prob = min(self.prob, 1)

        if self.prob < random.random():
            return
        content = message.content
        channel = message.channel
        for key in self.keywords:
            cur_time, last_time = time.time(), self.keywords[key][2]
            if key in content and cur_time - last_time > self.min_time_gap:
                data = self.keywords[key]
                await channel.send(self.keywords[key][0])
                self.keywords[key] = (data[0], data[1], time.time(), *data[3:])
                self.last_triggered_time = self.last_recover_time = time.time()
                self.prob /= 2
                break
        return
