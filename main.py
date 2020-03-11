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
from tools import Choose
from game import TestGame

class Koishi(object):
    def __init__(self):
        self.on_command_list = []
        self.on_reaction_list = []

        self.mention_context = KoishiMentionContext()
        self.jyanken = KoishiJyanken(self)
        self._help = KoishiHelp(self)
        self.laugh = KoishiLaugh(self)

        self.test_game = TestGame(self)
        self.choose = Choose(self)
        self.file_manager = FileManager(self, link_dict_path="link_dict.pickle")

    def regist_on_command(self, app):
        self.on_command_list.append(app)

    def regist_on_reaction(self, app):
        self.on_reaction_list.append(app)

client = discord.Client()
koishi = Koishi()


@client.event
async def on_ready():
    pass

async def mentioned_act(message):
    await koishi.mention_context.mentioned(message.channel)

@client.event
async def on_message(message):
    if message.author.bot:
        return
    # print(message.content)
    if message.content.lower().startswith(cfg.CMD_PREFIX):
        await utils.on_command(message, koishi)
        #await message.channel.send("!!")
    elif client.user in message.mentions:
        await mentioned_act(message)

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

client.run(TOKEN)

