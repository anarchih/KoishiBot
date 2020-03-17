import discord
import re
import config as cfg
import shlex
from aioconsole import ainput
import asyncio
import emoji


is_url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

async def send_image(channel, path, content=None):
    with open(path, 'rb') as f:
        picture = discord.File(f)
        await channel.send(content=content, file=picture)
    pass

def is_url(url):
    return re.match(is_url_regex, url) is not None

async def on_command(message, agent):
    content = message.content
    channel = message.channel
    # TODO: need better solution
    # Ignore the input with escaped character currently.
    try:
        content = content[len(cfg.CMD_PREFIX):]
        cmd_list = shlex.split(content)
    except ValueError:
        return None

    if len(cmd_list) == 0:
        return None

    cmd0 = cmd_list[0].lower()

    for app in agent.on_command_list:
        if await app.on_command(cmd0, cmd_list[1:], message):
            return
    await message.channel.send("Incorrect Command!")

def to_emoji(content, client):
    emojis = client.emojis
    img_emoji_dict = {e.name: str(e.id) for e in emojis if not e.animated}
    gif_emoji_dict = {e.name: str(e.id) for e in emojis if e.animated}
    candidates = re.findall("\s:(.+?):", content)
    candidates = list(set(candidates))
    new_content = content
    for c in candidates:
        if c in img_emoji_dict:
            _id = img_emoji_dict[c]
            new_content = re.sub("\s(:)(" + c + ")(:)", "<\g<1>\g<2>\g<3>" + _id + ">", content)
        elif c in gif_emoji_dict:
            _id = gif_emoji_dict[c]
            new_content = re.sub("\s(:)(" + c + ")(:)", "<a\g<1>\g<2>\g<3>" + _id + ">", content)

    return new_content

async def cli(client, default_channel_id):
    while True:
        if not client.is_ready():
            await asyncio.sleep(.5)
        else:
            break
    # init_channel = client.get_channel(684018621919264798)
    # init_message = await init_channel.send(":thonk:")
    # init_message.channel = None
    channel = client.get_channel(default_channel_id)
    guild = channel.guild
    while True:
        try:
            print(guild.name, channel.name)
            content = await ainput(">>> ")
            if content.startswith("@c"):
                cmd_list = shlex.split(content)
                if len(cmd_list) == 1:
                    print("\n".join([str(i) + " " + g.name for i, g in enumerate(client.guilds)]))
                elif len(cmd_list) == 2:
                    guild = [g for g in client.guilds if g.name == cmd_list[1]]
                    guild = guild[0] if len(guild) >= 1 else None
                    channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
                    print("\n".join([str(i) + " " + c.guild.name + " " + c.name for i, c in enumerate(channels)]))
                elif len(cmd_list) == 3:
                    t_g, t_c = cmd_list[1], cmd_list[2]
                    channels = list(client.get_all_channels())
                    target_channels = [c for c in channels if str(c.guild) == t_g and str(c) == t_c]
                    if len(target_channels) == 1:
                        channel  = target_channels[0]
                        guild = channel.guild

            elif content.startswith("@ra") or content.startswith("@rd"):
                cmd_list = shlex.split(content)
                if len(cmd_list) >= 3:
                    emoji_list = []
                    messages = await channel.history(limit=20).flatten()
                    try:
                        num = int(cmd_list[-1])
                        message = messages[num]
                    except:
                        print("Last Argument should be integer")

                    for cmd in cmd_list[1:-1]:
                        try:
                            cmd = emoji.emojize(cmd)
                            cmd = to_emoji(" " + cmd, client).strip()
                            if cmd_list[0] == "@ra":
                                await message.add_reaction(cmd)
                            else:
                                await message.remove_reaction(cmd, client.user)
                        except Exception as e:
                            print(e)
                            pass

            elif content.startswith("!"):
                content = to_emoji(content[1:], client)
                await channel.send(content)
        except KeyboardInterrupt as e:
            return
        except Exception as e:
            print(e)
