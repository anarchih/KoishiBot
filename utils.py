import discord
import re
import config as cfg
import shlex


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
