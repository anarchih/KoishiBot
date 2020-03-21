import discord
import random


class MahjongEmojiDisplay(object):
    def __init__(self, cmd_keys=["mahjong", "mj"]):
        self.cmd_keys = cmd_keys
        self.mj_dict = {
            "1m": "<:1m:690877262542667776>",
            "1p": "<:1p:690877262572158987>",
            "1s": "<:1s:690877263125676073>",
            "1z": "<:1z:690877263297773629>",
            "2m": "<:2m:690877263784181762>",
            "2p": "<:2p:690877263947890699>",
            "2z": "<:2z:690877264321183834>",
            "3p": "<:3p:690877264388161549>",
            "2s": "<:2s:690877264438624258>",
            "3m": "<:3m:690877264681893929>",
            "3s": "<:3s:690877264967106680>",
            "5z": "<:5z:690877265751310446>",
            "3z": "<:3z:690877266468798485>",
            "4z": "<:4z:690877267676495972>",
            "4m": "<:4m:690877268179943466>",
            "7z": "<:7z:690877268192657448>",
            "4s": "<:4s:690877268330807330>",
            "6z": "<:6z:690877268561494087>",
            "5s": "<:5s:690877268675002368>",
            "6m": "<:6m:690877268729397318>",
            "7m": "<:7m:690877268775534592>",
            "8m": "<:8m:690877268951564328>",
            "5m": "<:5m:690877269044101182>",
            "7s": "<:7s:690877269409005569>",
            "8p": "<:8p:690877269433909339>",
            "9s": "<:9s:690877269480308768>",
            "9m": "<:9m:690877269488435311>",
            "5p": "<:5p:690877269555806239>",
            "4p": "<:4p:690877269648080986>",
            "0s": "<:0s:690877269710995466>",
            "0m": "<:0m:690877269731966996>",
            "8s": "<:8s:690877269815722014>",
            "6s": "<:6s:690877269824110633>",
            "0p": "<:0p:690877269949808640>",
            "7p": "<:7p:690877269987557379>",
            "6p": "<:6p:690877269991882752>",
            "9p": "<:9p:690877270155329566>",
        }
    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1:
                s = self.resolve_string(args[0])
                if s:
                    await message.channel.send(s)
                else:
                    await message.channel.send("Illegal Input")

            return True
        else:
            return False

    def resolve_string(self, string):
        tiles = []
        tmps = []
        flag = False
        for c in string:
            if "0" <= c <= "9":
                tmps.append(c)
            elif c == "s" or c == "z" or c == "m" or c == "p":
                try:
                    tiles.extend([self.mj_dict[t + c] for t in tmps])
                except:
                    return None
                flag = True
                tmps = []
            else:
                return None
        if not flag:
            return None
        return "".join(tiles)

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

