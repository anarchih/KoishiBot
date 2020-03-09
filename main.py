import os
import time
import discord
from koishi_state import Koishi
from utils import send_image
import shlex
import random
from token_for_koishi import TOKEN

CMD_PREFIX = "k!"


client = discord.Client()
koishi = Koishi()

def split_command(content, num):
    cmd_list = content.split(None, num)
    if len(cmd_list) <= num:
        return None
    else:
        return cmd_list[num]


async def run_command(message):
    content = message.content
    channel = message.channel
    # TODO: need better solution
    # Ignore the input with escaped character currently.
    try:
        content = content[len(CMD_PREFIX):]
        cmd_list = shlex.split(content)
    except ValueError:
        return

    if len(cmd_list) == 0:
        return None
    cmd0 = cmd_list[0].lower()

    if cmd0 == "laugh":
        await send_image(channel, "happy.png")

    elif cmd0 == "jyanken" or cmd0 == "jk":
        if len(cmd_list) == 2:
            await koishi.jyanken.do_jyanken(channel, cmd_list[1])

    elif cmd0 == "game":
        await koishi.test_game.start(channel)

    elif cmd0 == "file":
        if len(cmd_list) >= 2:
            await koishi.file_manager.run(cmd_list[1:], message)

    elif cmd0 == "choose":
        if len(cmd_list) >= 2:
            r = random.randint(0, len(cmd_list) - 2)
            await message.channel.send(cmd_list[r + 1])
    elif cmd0 == "help":
        await message.channel.send("<https://www.notion.so/Koishi-Discord-Bot-b4fea743c6d049fab8d8e1a1c768f4d5>")
@client.event
async def on_ready():
    pass
# 0 normal, 1 annoy, 2 angry
async def mentioned_act(message):
    await koishi.mention_context.mentioned(message.channel)

@client.event
async def on_message(message):
    if message.author.bot:
        return
    # print(message.content)
    if message.content.lower().startswith(CMD_PREFIX):
        await run_command(message)
        #await message.channel.send("!!")
    elif client.user in message.mentions:
        await mentioned_act(message)

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if koishi.test_game.status == 1 and \
        reaction.message.id == koishi.test_game.game_message.id:
        await koishi.test_game.move(user, reaction.emoji)

    elif koishi.file_manager.list_message and \
        koishi.file_manager.list_message.id == reaction.message.id:
        await koishi.file_manager.change_list_page(reaction.emoji)

@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    if koishi.test_game.status == 1 and \
        reaction.message.id == koishi.test_game.game_message.id:
        await koishi.test_game.move(user, reaction.emoji)

    elif koishi.file_manager.list_message and \
        koishi.file_manager.list_message.id == reaction.message.id:
        await koishi.file_manager.change_list_page(reaction.emoji)

client.run(TOKEN)

