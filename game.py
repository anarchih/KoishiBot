
import discord
import time
from utils import send_image, is_url
import random
import numpy as np
import urllib
import imghdr
import os
import pickle
import math
import re
import asyncio


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


