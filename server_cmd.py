from aioconsole import ainput
import asyncio
import emoji
import discord
import re
import config as cfg
import shlex


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
                    guilds = [g for g in client.guilds if g.name == cmd_list[1]]
                    if len(guilds) >= 1:
                        guild = guilds[0]
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
                    except:
                        print("Last Argument should be integer")
                        continue
                    if 0 <= num < 20:
                        message = messages[num]
                    else:
                        try:
                            message = await channel.fetch_message(num)
                        except:
                            print("Unable to get the message")
                            continue

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
