import discord
import random

class Choose(object):
    def __init__(self, cmd_keys=["choose"]):
        self.cmd_keys = cmd_keys


    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) >= 1:
                r = random.randint(0, len(args) - 1)
                await message.channel.send(args[r])
            return True
        else:
            return False


class GuildReactionEcho(object):
    def __init__(self):
        pass

    async def on_message(self, message):
        emojis = message.channel.guild.emojis
        for emoji in emojis:
            if str(emoji) in message.content:
                await message.add_reaction(emoji)


