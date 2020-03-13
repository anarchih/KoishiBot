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
    # print(message.content)
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

from aioconsole import ainput
async def cli():
    while True:
        if not client.is_ready():
            await asyncio.sleep(.5)
        else:
            break
    # init_channel = client.get_channel(684018621919264798)
    # init_message = await init_channel.send(":thonk:")
    # init_message.channel = None
    channel = client.get_channel(684018621919264798)
    guild = channel.guild
    while True:
        print(guild.name, channel.name)
        content = await ainput(">>> ")
        if content.startswith("@c"):
            cmd_list = shlex.split(content)
            if len(cmd_list) == 1:
                channels = list(client.get_all_channels())
                print([(str(c.guild), str(c)) for c in channels])
            elif len(cmd_list) == 3:
                t_g, t_c = cmd_list[1], cmd_list[2]
                channels = list(client.get_all_channels())
                target_channels = [c for c in channels if str(c.guild) == t_g and str(c) == t_c]
                if len(target_channels) == 1:
                    channel  = target_channels[0]
                    guild = channel.guild

        elif content.startswith("!"):
            await channel.send(content[1:])

client.loop.create_task(cli())
client.run(TOKEN)

