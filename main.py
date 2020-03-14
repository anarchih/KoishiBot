import os
import time
import discord
import utils
import shlex
import random
import config as cfg
from token_for_koishi import TOKEN
from file_manager import FileManager
from koishi_cmd import *
from mixed_app import *
from game import TestGame

class Koishi(object):
    def __init__(self, client):
        self.on_command_list = []
        self.on_reaction_list = []
        self.on_message_list = []

        self.mention_context = KoishiMentionContext(self, client)
        self.jyanken = KoishiJyanken(self)
        self._help = KoishiHelp(self)
        self.laugh = KoishiLaugh(self)
        self.reaction_echo = KoishiReactionEcho(self)

        self.test_game = TestGame(self)
        self.choose = Choose(self)
        self.file_manager = FileManager(self, link_dict_path="link_dict.pickle")

    def regist_on_command(self, app):
        self.on_command_list.append(app)

    def regist_on_reaction(self, app):
        self.on_reaction_list.append(app)

    def regist_on_message(self, app):
        self.on_message_list.append(app)

client = discord.Client()
koishi = Koishi(client)


@client.event
async def on_ready():
    pass


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
client.run(TOKEN)

