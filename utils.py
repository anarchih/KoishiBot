import discord
import re
import config as cfg
import shlex
import aiohttp


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
        return False

    if len(cmd_list) == 0:
        return False

    cmd0 = cmd_list[0].lower()

    for app in agent.event_dict["on_command"]:
        if await app.on_command(cmd0, cmd_list[1:], message):
            return True
    await message.channel.send("Incorrect Command!")
    return False


async def get_data_by_url(url):
    async with aiohttp.ClientSession() as client:
        async with client.get(str(url)) as res:
            return await res.read()


def get_user_by_name(name, guild):
    members = guild.members
    # Check Mention
    try:
        _id = int(re.findall("<@!([0-9]+)>", name)[0])
        for m in members:
            if m.id == _id:
                return m
        return None
    except Exception as e:
        pass

    # Check Nick
    for m in members:
        if m.nick == name:
            return m

    # Check Name
    for m in members:
        if m.name == name:
            return m

    return None

async def delete_message(message):
    try:
        await message.delete()
        return True
    except Exception as e:
        return False
