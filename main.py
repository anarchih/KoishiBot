import os
import time
import discord
import utils
import shlex
import random
import config as cfg
import discord_token as token
from file_manager import FileManager
from koishi_cmd import *
from mixed_app import *
from game import TestGame
from caption_generator import ImageText

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

            ImageText(),
            TestGame(),
            Choose(),
            FileManager(link_dict_path="link_dict.pickle")
        ]

        self.regist_events()

    def regist_events(self):
        self.on_command_list = []
        self.on_reaction_list = []
        self.on_message_list = []
        self.on_ready_list = []

        for app in self.applications:
            app_dict = app.__class__.__dict__
            if "on_command" in app_dict:
                self.on_command_list.append(app)
            if "on_reaction" in app_dict:
                self.on_reaction_list.append(app)
            if "on_message" in app_dict:
                self.on_message_list.append(app)
            if "on_ready" in app_dict:
                self.on_ready_list.append(app)

client = discord.Client()
koishi = Koishi(client)


@client.event
async def on_ready():
    for app in koishi.on_ready_list:
        await app.on_ready(client)


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower().startswith(cfg.CMD_PREFIX):
        await utils.on_command(message, koishi)

    for app in koishi.on_message_list:
        await app.on_message(message)

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    for app in koishi.on_reaction_list:
        await app.on_reaction(reaction, user)

@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    for app in koishi.on_reaction_list:
        await app.on_reaction(reaction, user)


client.loop.create_task(utils.cli(client, default_channel_id=483590049263517696))
client.run(token.KOISHI)

