import os
import time
import discord
import utils
import shlex
import random
import config as cfg
import inspect
import discord_token as token
from file_manager import FileManager
from koishi_cmd import *
from mixed_app import *
from game import TestGame, Balloon, Puzzle
from caption_generator import BaseCaption
from keyword_reply import KeywordReply
from server_cmd import cli
from stat_cmd import StatEmoji
from mahjong import Mahjong
import user
from image_processing import ImageProcessing
from cvpr import ImageLabel


us = user.UserSystem()

class Koishi(object):
    def __init__(self, client):
        self.on_command_list = []
        self.on_reaction_list = []
        self.on_message_list = []
        self.applications = [
            KoishiMentionContext(),
            KoishiJyanken(),
            KoishiLaugh(),
            KoishiReactionEcho(),

            # BaseCaption(cmd_keys=["test"]),
            KeywordReply(keywords_path="keywords.pickle", min_time_gap=60*10, recover_time=60*60*2),
            KoishiSimpleCaption(),
            Choose(),
            StatEmoji(how_long=7 * 4),
            Mahjong(),
            FileManager(link_dict_path="link_dict.pickle"),
            History(),
            EmojiRaw(),
            Puzzle(735780993784610816, prefix="koishi"),
            ImageProcessing(),
            LinkExtractor(),
            # Balloon(us=us),
            Help(self),
            # us,
        ]

        self.regist_events()

    def regist_events(self):
        # event_s = [self.on_command_list, self.on_reaction_list, self.on_message_list, self.on_ready_list]
        self.event_dict = {
            "on_command": [],
            "on_reaction": [],
            "on_raw_reaction": [],
            "on_message": [],
            "on_ready": [],
            "on_time": [],
        }
        for event_name, event_list in self.event_dict.items():
            for app in self.applications:
                for _cls in inspect.getmro(app.__class__)[:-1]:
                    app_dict = _cls.__dict__
                    if event_name in app_dict:
                        event_list.append(app)
                        break

client = discord.Client()
koishi = Koishi(client)


@client.event
async def on_ready():
    for app in koishi.event_dict['on_ready']:
        await app.on_ready(client)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    is_command = False
    if message.content.lower().startswith(cfg.CMD_PREFIX):
        await utils.on_command(message, koishi)
    else:
        for app in koishi.event_dict['on_message']:
            await app.on_message(message)

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    for app in koishi.event_dict['on_reaction']:
        await app.on_reaction(reaction, user)

@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    for app in koishi.event_dict['on_reaction']:
        await app.on_reaction(reaction, user)

@client.event
async def on_raw_reaction_add(payload):
    for app in koishi.event_dict['on_raw_reaction']:
        await app.on_raw_reaction(payload)

async def on_time(client):
    sleep_time = 10
    while True:
        start_time = time.time()
        for app in koishi.event_dict['on_time']:
            await app.on_time(client)
        sleep_time = 10 - (time.time() - start_time)
        await asyncio.sleep(sleep_time)


client.loop.create_task(on_time(client))
client.loop.create_task(cli(client, default_channel_id=483590049263517696))
client.run(token.KOISHI)

