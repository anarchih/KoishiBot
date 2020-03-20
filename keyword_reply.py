import pickle
import discord
import time
import os
import random

class KeywordReply(object):
    def __init__(self, keywords_path, min_time_gap, prob, cmd_keys=["keyword"]):
        self.cmd_keys = cmd_keys
        self.keywords_path = keywords_path
        self.min_time_gap = min_time_gap
        self.prob = prob
        self.last_triggered_time = 0
        self.command_lock = False

        if not os.path.exists(self.keywords_path):
            with open(self.keywords_path, "wb") as f:
                pickle.dump({}, f)

        with open(self.keywords_path, "rb") as f:
            self.keywords = pickle.load(f)


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 3 and args[0] == "save":
                await self.save_keyword(args, message.author)
            elif len(args) == 2 and args[0] == "delete":
                await self.delete_keyword(args)
            elif len(args) == 3 and args[0] == "rename":
                await self.rename_keyword(args, message.author)
            else:
                return True

            return True
        return False
    def save_to_file(self):
        with open(self.keywords_path, "wb") as f:
            pickle.dump(self.keywords, f)

    async def save_keyword(self, args, author):
        self.keywords[args[1]] = (args[2], 1, 0, str(author), author.id)
        self.save_to_file()

    async def delete_keyword(self, args):
        key = args[1]
        if key in self.keywords:
            del self.keywords[key]
            self.save_to_file()

    async def rename_keyword(self, args, author):
        old_key, new_key = args[1], args[2]
        if old_key in self.keywords:
            data = self.keywords[old_key]
            del self.keywords[old_key]
            self.keywords[new_key] = (*data[0:3], str(author), author.id)
            self.save_to_file()

    async def on_message(self, message):
        if self.command_lock:
            self.command_lock = False
            return
        if time.time() - self.last_triggered_time < self.min_time_gap:
            return
        if self.prob > random.random():
            return
        content = message.content
        channel = message.channel
        for key in self.keywords:
            if key in content and time.time() - self.keywords[key][2] > self.min_time_gap:
                await channel.send(self.keywords[key][0])
                data = self.keywords[key]
                self.keywords[key] = (data[0], data[1], time.time(), *data[3:])
                self.last_triggered_time = time.time()
                break
        return
