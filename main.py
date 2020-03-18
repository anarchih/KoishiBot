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
from game import TestGame
from caption_generator import BaseCaption

class Koishi(object):
    def __init__(self, client):
        self.on_command_list = []
        self.on_reaction_list = []
        self.on_message_list = []
        self.applications = [
            KoishiMentionContext(),
            KoishiJyanken(),
            KoishiHelp(),
            KoishiLaugh(),
            KoishiHelp(),
            KoishiLaugh(),
            KoishiReactionEcho(),

            # BaseCaption(),
            KoishiSimpleCaption(),
            TestGame(),
            Choose(),
            FileManager(link_dict_path="link_dict.pickle")
        ]

        self.regist_events()

    def regist_events(self):
        # event_s = [self.on_command_list, self.on_reaction_list, self.on_message_list, self.on_ready_list]
        self.event_dict = {
            "on_command": [],
            "on_reaction": [],
            "on_message": [],
            "on_ready": [],
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
    if message.content.lower().startswith(cfg.CMD_PREFIX):
        await utils.on_command(message, koishi)

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


client.loop.create_task(utils.cli(client, default_channel_id=483590049263517696))
client.run(token.KOISHI)

