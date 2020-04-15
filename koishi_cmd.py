import discord
import time
import utils
import random
import numpy as np
import urllib
import imghdr
import os
import pickle
import math
import re
import asyncio
import PIL
from caption_generator import BaseCaption
PATIENT_TIME = 120
RECOVER_TIME = 120


class KoishiSimpleCaption(BaseCaption):
    def __init__(self, cmd_keys=["caption"]):
        super(KoishiSimpleCaption, self).__init__(cmd_keys)

        self.margin_top_w, self.margin_top_b = 0, 80
        self.margin_right_w, self.margin_right_b = 0, 40
        self.margin_left_w, self.margin_left_b = 0, 40

        self.margin_color = (255, 255, 255, 255)
        self.text_color = (0, 0, 0, 0)
        self.text_min_size, self.text_max_size = 12, 36
        self.text_width_w, self.text_width_b = .9, 0
        self.text_height_w, self.text_height_b = 0, self.margin_top_b * .9
        self.text_y_w, self.text_y_b = .0, self.margin_top_b / 2

        self.image_list = [
            "annoyed", "angry", "cry",
            "ya", "ridicule", "laugh",
            "excited", "displeased", "facepalm"
        ]

    def get_image(self, args, message):
        try:
            arg = args[1]
        except:
            r = random.randint(0, len(self.image_list) - 1)
            arg = self.image_list[r]

        for filename in self.image_list:
            if arg == filename:
                filename = filename +".png"
                return PIL.Image.open(filename), None

        return None, "Legal keywords: " + ", ".join(self.image_list)
        filename = self.image_list[0] +".png"

class KoishiReactionEcho(object):
    def __init__(self):
        # Possible to be removed/modified by the guild admin
        self.emoji_dict = {
            "Koishi_smile": 681346761012412538,
            "Koishi_shock": 686589788546924559,
            "Koishi_shiny_eye": 687625146466304031,
            "Koishi_secretly_watching": 675593130040623117,
            "Koishi_cry": 686589787255341066,
        }
        self.gif_emoji_dict = {
            "Koishi_play_hat": 686603096495095815,
            "Koishi_facial_expressions": 686589788903571488,
        }


    async def on_message(self, message):
        emojis = message.channel.guild.emojis
        img_emoji_dict = {e.name: e.id for e in emojis if "Koishi" in e.name and not e.animated}
        gif_emoji_dict = {e.name: e.id for e in emojis if "Koishi" in e.name and e.animated}
        for name, _id in img_emoji_dict.items():
            emoji = "<:%s:%d>" % (name, _id)
            if emoji in message.content:
                await message.add_reaction(emoji)
        for name, _id in gif_emoji_dict.items():
            emoji = "<a:%s:%d>" % (name, _id)
            if emoji in message.content:
                await message.add_reaction(emoji)


class KoishiStatus(object):
    def __init__(self):
        self.happiness = 0
        self.favorability = 0



class KoishiLaugh(object):
    def __init__(self, cmd_keys=["laugh"]):
        self.cmd_keys = cmd_keys


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            await utils.send_image(message.channel, "laugh.png")
            return True
        else:
            return False


class KoishiHelp(object):
    def __init__(self, cmd_keys=["help"]):
        self.cmd_keys = cmd_keys


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            await message.channel.send("<https://hackmd.io/Ds0MR940RcqvM29ODKjiBg>")
            return True
        else:
            return False

class KoishiJyanken(object):
    def __init__(self, cmd_keys=["jyanken", "jk"]):
        self.cmd_keys = cmd_keys
        self.act_dict = {
            0: "✌️",
            1: "✊",
            2: "🖐️",
            3: "🖕",
        }
        self.reversed_act_dict = {v: k for k, v in self.act_dict.items()}
        self.refused_time = 0


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1:
                await self.do_jyanken(message.channel, args[0])
            return True
        return False

    async def do_jyanken(self, channel, other_act_key):
        try:
            if other_act_key not in self.reversed_act_dict:
                return

            other_act = self.reversed_act_dict[other_act_key]

            if other_act == 3:
                await utils.send_image(channel, "displeased.png")
                self.refused_time = time.time()
                return

            if time.time() - self.refused_time < 60:
                await utils.send_image(channel, "annoyed.png")
                return

            act = random.randint(0, 2)
            react = random.randint(0, 1)
            # Middle Finger Case
            if (act - other_act) % 3 == 0:
                if react: await utils.send_image(channel, "excited.png", self.act_dict[act])
                else: await utils.send_image(channel, "facepalm.png", self.act_dict[act])
            elif (act - other_act) % 3 == 1:
                if react: await utils.send_image(channel, "ya.png", self.act_dict[act])
                else: await utils.send_image(channel, "ridicule.png", self.act_dict[act])
            else:
                if react: await utils.send_image(channel, "angry.png", self.act_dict[act])
                else: await utils.send_image(channel, "cry.png", self.act_dict[act])
        except Exception as e:
            print(e)
class KoishiMentionContext(object):
    def __init__(self, state=None):
        self.client = None
        self.time_list = [0, 0, 0]
        if not state:
            self.transition_to(NormalState())
        else:
            self.transition_to(state)

    def update_time_list(self):
        mentioned_time = time.time()
        self.time_list.append(mentioned_time)
        self.time_list = self.time_list[1:]

    def clear_time_list_except_latest(self):
        self.time_list = [0, 0, self.time_list[-1]]

    def clear_time_list(self):
        self.time_list = [0, 0, 0]

    def transition_to(self, state):
        self._state = state
        self._state.context = self

    async def on_message(self, message):
        if self.client and self.client.user in message.mentions:
            await self.mentioned(message.channel)

    async def on_ready(self, client):
        self.client = client

    async def mentioned(self, channel):
        await self._state.send_action(channel)

class State(object):
    def send_reaction(self):
        pass
        #await send_image()

class NormalState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[0] <= PATIENT_TIME:
            self.context.transition_to(AnnoyState())
            self.context.clear_time_list_except_latest()
        await utils.send_image(channel, "laugh.png")

class AnnoyState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[-2] >= RECOVER_TIME:
            self.context.clear_time_list()
            self.context.transition_to(NormalState())
            await self.context.mentioned(channel)
            return

        elif time_list[-1] - time_list[0] <= PATIENT_TIME:
            self.context.clear_time_list_except_latest()
            self.context.transition_to(AngryState())

        await utils.send_image(channel, "annoy.png")

class AngryState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[-2] >= RECOVER_TIME:
            self.context.clear_time_list()
            self.context.transition_to(NormalState())
            await self.context.mentioned(channel)
            return

        await utils.send_image(channel, "angry.png")

