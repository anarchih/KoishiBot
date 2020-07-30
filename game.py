import discord
import time
from utils import send_image, is_url, get_data_by_url
import random
import numpy as np
import urllib
import imghdr
import os
import pickle
import math
import re
import asyncio
import random
from PIL import Image
import time
import aiohttp
import io


class Puzzle(object):
    def __init__(self, guild_id, prefix, cmd_keys=["puzzle"]):
        self.cmd_keys = cmd_keys
        self.emoji_str_prefix = "puzzle_" + prefix + "_"
        self.num_of_squares = 3
        self.emoji_guild_id = guild_id
        self.emoji_guild = None
        self.cool_down = 900
        self.reaction_list = ["⬅️", "⬇️", "⬆️", "➡️"]

        self.hole_emoji_str = "<:nil:735852429391953920>"
        self.last_execute_time = 0

        self.game_message = None
        self.emoji_str_list = []
        self.idx_matrix = None
        self.description = '\n'.join([
            "N-puzzle 遊戲",
            "- start ",
            "  使用此指令需要上傳一張圖片，此指令會建立基於該圖片的 N-puzzle 遊戲",
            "",
            "- restart",
            "  使用最後一次上傳的圖片重新開始遊戲",
            "",
            "- resume",
            "  繼續遊戲",
        ])

    def gen_n_puzzle(self, n):
        idx_matrix = np.arange(0, n ** 2).reshape(n, n)
        i, j = random.randint(0, n - 1), random.randint(0, n - 1)
        count = 0
        while count < 200:
            r = random.randint(0, 3)
            if r == 0 and i - 1 >= 0:
                idx_matrix[i, j], idx_matrix[i - 1, j] = idx_matrix[i - 1, j], idx_matrix[i, j]
                i -= 1
            elif r == 1 and i + 1 < n:
                idx_matrix[i, j], idx_matrix[i + 1, j] = idx_matrix[i + 1, j], idx_matrix[i, j]
                i += 1
            elif r == 2 and j - 1 >= 0:
                idx_matrix[i, j], idx_matrix[i, j - 1] = idx_matrix[i, j - 1], idx_matrix[i, j]
                j -= 1
            elif r == 3 and j + 1 < n:
                idx_matrix[i, j], idx_matrix[i, j + 1] = idx_matrix[i, j + 1], idx_matrix[i, j]
                j += 1
            else:
                count -=1
            count += 1
        v = idx_matrix[i, j]
        idx_matrix[i, j] = -1
        return idx_matrix, i, j, v



    async def on_ready(self, client):
        self.emoji_guild = client.get_guild(self.emoji_guild_id)

    async def clean_emojis(self):
        for e in self.emoji_guild.emojis:
            if e.name.startswith(self.emoji_str_prefix):
                await e.delete()


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1 and args[0] == "start":
                await self.run_start(message)
            elif len(args) == 1 and args[0] == "restart":
                await self.run_restart(message)
            elif len(args) == 1 and args[0] == "resume":
                await self.run_resume(message)
            return True

    async def run_resume(self, message):
        if self.emoji_str_list and self.idx_matrix is not None:
            s = self.get_game_str()
            self.game_message = await message.channel.send(s)
            for reaction in self.reaction_list:
                await self.game_message.add_reaction(reaction)
        else:
            await message.channel.send("No active game.")

    async def run_restart(self, message):
        if self.emoji_str_list:
            while True:
                self.idx_matrix, self.hole_y, self.hole_x, self.hole_v = self.gen_n_puzzle(self.num_of_squares)
                if not self.check_win():
                    break

            await self.run_resume(message)
        else:
            await message.channel.send("No Cached Image.")

    async def create_emojis(self, img_arr):
        size = min(img_arr.shape[0:2])
        size -= size % self.num_of_squares
        sub_img_size = size // self.num_of_squares
        start_y = (img_arr.shape[0] - size)// 2
        start_x = (img_arr.shape[1] - size)// 2
        img_arr = img_arr[start_y: start_y + size, start_x: start_x + size]

        sub_imgs = []
        for i in range(self.num_of_squares):
            for j in range(self.num_of_squares):
                h_min, h_max = i * sub_img_size, (i + 1) * sub_img_size
                w_min, w_max = j * sub_img_size, (j + 1) * sub_img_size
                sub_img = img_arr[h_min: h_max, w_min: w_max]
                sub_imgs.append(sub_img)

        for i, sub_img in enumerate(sub_imgs):
            with io.BytesIO() as f:
                Image.fromarray(sub_img).save(f, 'png')
                byte = f.getvalue()
                emoji = await self.emoji_guild.create_custom_emoji(name=self.emoji_str_prefix + "%d".zfill(2) % i,image=byte)
                self.emoji_str_list.append("<:%s:%d>" % (emoji.name, emoji.id))

    async def run_start(self, message):
        if time.time() - self.last_execute_time < self.cool_down:
            await message.channel.send("Please wait for %d seconds." % (self.cool_down + self.last_execute_time - time.time()))
        elif not message.attachments:
            await message.channel.send("No attachment.")
        else:
            attachment = message.attachments[0]
            url, filename_ext = attachment.url, attachment.filename
            img_bytes = await get_data_by_url(url)
            try:
                img_arr = np.array(Image.open(io.BytesIO(img_bytes)))
            except OSError:
                await message.channel.send("Please upload image.")
                return
            await message.channel.send("Game is in preparation.")
            await self.clean_emojis()
            await self.create_emojis(img_arr)
            self.last_execute_time = time.time()
            await self.run_restart(message)

        return True

    async def on_reaction(self, reaction, user):
        if self.game_message and reaction.message.id == self.game_message.id:
            await self.move(reaction.emoji, user)

    def check_win(self):
        n = self.num_of_squares
        for i in range(n):
            for j in range(n):
                if self.idx_matrix[i, j] == -1:
                    if self.hole_v != i * n + j:
                        return False
                else:
                    if self.idx_matrix[i, j] != i * n + j:
                        return False
        return True
    async def move(self, emoji, user):
        if self.game_message:
            hy, hx = self.hole_y, self.hole_x
            n = self.num_of_squares
            if emoji == self.reaction_list[3] and hx - 1 >= 0:
                self.idx_matrix[hy][hx], self.idx_matrix[hy][hx - 1] = self.idx_matrix[hy][hx - 1], self.idx_matrix[hy][hx]
                self.hole_x -= 1
            elif emoji == self.reaction_list[0] and hx + 1 < n:
                self.idx_matrix[hy][hx], self.idx_matrix[hy][hx + 1] = self.idx_matrix[hy][hx + 1], self.idx_matrix[hy][hx]
                self.hole_x += 1
            elif emoji == self.reaction_list[1] and hy - 1 >= 0:
                self.idx_matrix[hy][hx], self.idx_matrix[hy - 1][hx] = self.idx_matrix[hy - 1][hx], self.idx_matrix[hy][hx]
                self.hole_y -= 1
            elif emoji == self.reaction_list[2] and hy + 1 < n:
                self.idx_matrix[hy][hx], self.idx_matrix[hy + 1][hx] = self.idx_matrix[hy + 1][hx], self.idx_matrix[hy][hx]
                self.hole_y += 1

            is_win = self.check_win()
            if is_win:
                self.idx_matrix[self.hole_y, self.hole_x] = self.hole_v

            s = self.get_game_str()
            await self.game_message.edit(content=s)

            if is_win:
                self.idx_matrix = None
                self.game_message = None

    def get_game_str(self):
        s = ""
        n = self.num_of_squares
        for i in range(n):
            for j in range(n):
                if self.idx_matrix[i][j] == -1:
                    s += self.hole_emoji_str
                else:
                    s += self.emoji_str_list[self.idx_matrix[i][j]]
            s += "\n"
        return s
"""
class KoishiTestGame(object):
    def __init__(self):
        self.game_message = None
        self.map_dict = {
            0: "⬛",
            1: "🔺",
            2: "◽"
        }
        #self.reaction_list = ["⬅️", "⬇️", "⬆️", "➡️"]
        self.reaction_list = ["⬅️", "➡️"]

    async def start(self, channel):
        self.generate_map()
        await self.send_map(channel)
        await self.add_reactions()

    async def send_map(self, channel):
        map_str = self.map2str()
        self.game_message = await channel.send(map_str)

    async def update_map(self):
        map_str = self.map2str()
        await self.game_message.edit(content=map_str)

    async def add_reactions(self):
        message = self.game_message
        for reaction in self.reaction_list:
            await message.add_reaction(reaction)

    def generate_map(self):
        self._map = np.zeros((9, 9))
        self._map[8, 4] = 1
        self.pos_y, self.pos_x = 8, 4

    def map2str(self):
        map_list = self._map.tolist()
        height, width = self._map.shape
        map_str = ""
        for i in range(height):
            for j in range(width):
                key = map_list[i][j]
                map_list[i][j] = self.map_dict[key]
            map_str += "".join(map_list[i]) + "\n"
        return map_str

    async def move(self, reaction):
        self._map[self.pos_y][self.pos_x] = 0
        print(reaction, self.reaction_list[0])
        if reaction == self.reaction_list[0]:
            self.pos_x = (self.pos_x - 1) % 9
        #elif reaction == self.reaction_list[1]:
        #    self.pos_y = (self.pos_y + 1) % 9
        #elif reaction == self.reaction_list[2]:
        #    self.pos_y = (self.pos_y - 1) % 9
        elif reaction == self.reaction_list[3]:
            self.pos_x = (self.pos_x + 1) % 9

        self._map[self.pos_y][self.pos_x] = 1

        await self.update_map()
"""
class TestGame(object):
    def __init__(self, cmd_keys=["game"]):
        self.game_message = None
        self.cmd_keys = cmd_keys
        self.status = 0
        self.score = 0
        self.map_dict = {
            0: "⬛",
            1: "🔺",
            2: "◽",
            3: "❌"
        }
        self.reaction_list = ["⬅️", "⏸️", "➡️"]


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            await self.start(message.channel)
            return True
        return False

    async def start(self, channel):
        self.generate_map()
        await self.send_map(channel)
        await self.add_reactions()
        self.status = 1
        self.score = 0

    async def send_map(self, channel, postfix="."):
        map_str = "Score: " + str(self.score) + "\n"
        map_str += self.map2str()
        map_str += "\n\n\n\n" + postfix
        self.game_message = await channel.send(map_str)

    async def update_map(self, postfix="."):
        map_str = "Score: " + str(self.score) + "\n"
        map_str += self.map2str()
        map_str += "\n\n\n\n" + postfix
        await self.game_message.edit(content=map_str)

    async def add_reactions(self):
        message = self.game_message
        for reaction in self.reaction_list:
            await message.add_reaction(reaction)

    def generate_map(self):
        self._map = np.zeros((9, 9))
        self._map[8, 4] = 1
        self.pos_y, self.pos_x = 8, 4

    def map2str(self):
        map_list = self._map.tolist()
        height, width = self._map.shape
        map_str = ""
        for i in range(height):
            for j in range(width):
                key = map_list[i][j]
                map_list[i][j] = self.map_dict[key]
            map_str += "".join(map_list[i]) + "\n"
        return map_str

    async def send_lose_info(self, name):
        self.status = 0
        await self.update_map(postfix=name + " Lose")

    async def on_reaction(self, reaction, user):
        if self.status == 1 and reaction.message.id == self.game_message.id:
            await self.move(reaction.emoji, user)

    async def move(self, reaction, user):
        if not self.status:
            return

        # Character Update
        if reaction == self.reaction_list[0]:
            self.pos_x = (self.pos_x - 1) % 9
        elif reaction == self.reaction_list[1]:
            pass
        elif reaction == self.reaction_list[2]:
            self.pos_x = (self.pos_x + 1) % 9
        else:
            return

        # Environment Update
        self._map = np.roll(self._map, shift=1, axis=0)
        self._map[0] = 0
        r = random.randint(0, 1)
        if r:
            r_pos = random.randint(0, self._map.shape[1] - 1)
            self._map[0, r_pos] = 2

        self.score += 1

        if self._map[self.pos_y][self.pos_x] == 0:
            self._map[self.pos_y][self.pos_x] = 1
            await self.update_map()
        else:
            self._map[self.pos_y][self.pos_x] = 3
            self.status = 0
            await self.send_lose_info(user.name)


