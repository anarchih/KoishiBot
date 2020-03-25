import discord
import time
from utils import send_image, is_url
import random
import numpy as np
import urllib
import imghdr
import os
import pickle
import math
import re
import asyncio
class ListMessageItem(object):
    def __init__(self, message, display, page, time):
        self.message = message
        self.display = display
        self.page = page
        self.time = time


class FileManager(object):
    def __init__(self, link_dict_path, cmd_keys=["file"]):
        self.link_dict_path = link_dict_path
        self.cmd_keys = cmd_keys
        self.list_keywords = ["list", "ls", "l"]
        self.rlist_keywords = ["rlist", "rls", "rl"]
        self.save_keywords = ["save", "sv", "s"]
        self.delete_keywords = ["delete", "del", "d"]
        self.author_keywords = ["author", "a"]
        self.rename_keywords = ["rename", "rn"]
        self.keywords = sum([
            self.list_keywords,
            self.rlist_keywords,
            self.save_keywords,
            self.delete_keywords,
            self.author_keywords,
            self.rename_keywords
        ], [])

        self.max_name_size = 100

        if not os.path.exists(self.link_dict_path):
            with open(self.link_dict_path, "wb") as f:
                pickle.dump({}, f)

        self.list_dict = {}
        self.max_list_num = 10
        self.page_size = 20
        self.page_reaction_list = ["⬅️", "➡️"]


    def add_name_list(self, name):
        if name < self.name_list[0]:
            self.name_list.insert(0, name)
        else:
            for i, n in enumerate(self.name_list):
                if n > name:
                    self.name_list.insert(i, name)
                    break

    def del_name_list(self, name):
        self.name_list.remove(name)

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys and len(args) >= 1:
            await self.run(args, message)
            return True
        return False

    async def run(self, sub_cmd_list, message):
        cmd = sub_cmd_list[0].lower()
        if cmd in self.list_keywords:
            await self._list("", message.channel)
        elif cmd in self.rlist_keywords:
            if len(sub_cmd_list) == 2:
                await self._list(sub_cmd_list[1], message.channel)

        elif cmd in self.save_keywords:
            if len(sub_cmd_list) == 2:
                await self.save_file(sub_cmd_list[1].lower(), message)
            elif len(sub_cmd_list) == 3:
                await self.save_url(sub_cmd_list[1].lower(), sub_cmd_list[2], message)

        elif cmd in self.delete_keywords:
            if len(sub_cmd_list) == 2:
                await self.delete(sub_cmd_list[1].lower(), message.channel)
        elif cmd in self.author_keywords:
            if len(sub_cmd_list) == 2:
                await self.show_author(sub_cmd_list[1].lower(), message.channel)
        elif cmd in self.rename_keywords:
            if len(sub_cmd_list) == 3:
                await self.rename(sub_cmd_list[1].lower(), sub_cmd_list[2].lower(), message.channel)
        else:
            await self.show(cmd, message.channel)

    def save_attachment_link(self, name, attachment, user):
        url, filename_ext = attachment.url, attachment.filename
        filename, file_ext = os.path.splitext(filename_ext)
        """
        ext = None
        if data[6:10] in (b'JFIF', b'Exif'):
            ext = ".jpg"
        elif data.startswith(b'\211PNG\r\n\032\n'):
            ext = ".png"
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            ext = ".gif"
        else:
            return -1
        """
        if os.path.exists(self.link_dict_path):
            with open(self.link_dict_path, 'rb') as f:
                link_dict = pickle.load(f)
            link_dict[name] = (url, filename, file_ext, str(user), user.id)
            with open(self.link_dict_path, "wb") as f:
                pickle.dump(link_dict, f)

        return 0

    async def is_name_valid(self, name, channel=None, send_error=False):
        if not channel and not send_error:
            raise Exception

        if name in self.keywords:
            if send_error:
                await channel.send("Failed to Save: Do not use the keywords.")
            return False
        elif len(name) > self.max_name_size:
            if send_error:
                await channel.send(
                    "Failed to Save: length of {} should not be > {}".format(
                        name,
                        self.max_name_size
                    )
                )
            return False
        return True

    async def save_url(self, name, url, message):
        name = name.lower()
        user = message.author
        channel = message.channel
        if not await self.is_name_valid(name, send_error=True, channel=channel):
            return
        elif not is_url(url):
            await channel.send("Failed to Save: It's not a legal url")
        elif len(url) > 1000:
            await channel.send("Failed to Save: Length of link should not be > 1000")
        else:
            with open(self.link_dict_path, 'rb') as f:
                link_dict = pickle.load(f)
            link_dict[name] = (url, "", "", str(user), user.id)
            with open(self.link_dict_path, "wb") as f:
                pickle.dump(link_dict, f)
            await channel.send("Successfully Saved")

    async def save_file(self, name, message):
        name = name.lower()
        channel = message.channel
        if not await self.is_name_valid(name, send_error=True, channel=channel):
            return
        try:
            if len(message.attachments) > 0:
                ret = self.save_attachment_link(name, message.attachments[0], message.author)
            else:
                await channel.send("Failed to Save: No attachment")
                return

            if ret == -1:
                await channel.send("Failed to Save: Unknown File Type (jpg, png & gif only)")
            elif ret == 0:
                await channel.send("Successfully Saved")
        except Exception as e:
            print(e)
            await channel.send("Failed to Save: Unknown Error")

    async def show_list(self, display_list, message=None, channel=None):
        display_list += [""] * (self.page_size - len(display_list))
        s = "Existing Files:\n- "
        s += "\n- ".join(display_list)
        if channel:
            return await channel.send(content=s)
        elif message:
            return await message.edit(content=s)
        else:
            return None

    async def _list(self, regex, channel):
        with open(self.link_dict_path, "rb") as f:
            display_list = list(pickle.load(f))
        if regex:
            display_list = [name for name in display_list if re.search(regex, name)]

        display_list.sort()

        list_message = await self.show_list(display_list[:self.page_size], None, channel)

        if not list_message:
            return

        for reaction in self.page_reaction_list:
            await list_message.add_reaction(reaction)

        if len(self.list_dict) >= self.max_list_num:
            min_item = min(self.list_dict.values(), key=lambda x: x.time)
            del self.list_dict[min_item.message.id]

        self.list_dict[list_message.id] = ListMessageItem(list_message, display_list, 0, time.time())


    async def on_reaction(self, reaction, user):
        msg_id = reaction.message.id
        if msg_id in self.list_dict:
            await self.change_list_page(reaction)
        if msg_id in self.question_dict:
            await self.replace_message(reaction)

    async def change_list_page(self, reaction):
        emoji, message = reaction.emoji, reaction.message
        list_item = self.list_dict[message.id]
        if emoji == self.page_reaction_list[0]:
            list_item.page -= 1
        elif emoji == self.page_reaction_list[1]:
            list_item.page += 1
        else:
            return

        display_list = list_item.display
        total_pages = math.ceil(len(display_list) / self.page_size)
        try:
            list_item.page %= total_pages
        except:
            return

        #
        start = list_item.page * self.page_size
        end = start + self.page_size
        display_list = display_list[start: end]
        await self.show_list(display_list, message)

    async def delete(self, name, channel):
        name = name.lower()
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        if name in link_dict:
            del link_dict[name]

        else:
            await channel.send("Failed to Delete: {} is not in the list".format(name))
            return

        with open(self.link_dict_path, "wb") as f:
            pickle.dump(link_dict, f)

        await channel.send("Successfully Deleted")

    async def show(self, name, channel):
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        name = name.lower()
        if name in link_dict:
            if link_dict[name][1] == "" and link_dict[name][2] == "":
                url = "\n{}".format(link_dict[name][0])
                await channel.send(url)
            else:
                opener = urllib.request.URLopener()
                opener.addheader('User-Agent', 'whatever')
                res = opener.open(link_dict[name][0])
                if res.code == 200:
                    import io
                    filename = link_dict[name][1] + link_dict[name][2]
                    d_file = discord.File(filename=filename, fp=io.BytesIO(res.file.fp.read()))
                    await channel.send(file=d_file)
                else:
                    await channel.send("Link is lost")
        else:
            await channel.send("Failed: {} is not in the list".format(name))

    async def show_author(self, name, channel):
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        name = name.lower()
        if name in link_dict:
            author_name, author_id = link_dict[name][3], link_dict[name][4]
            await channel.send("Author Name: {}\nAuthor ID: {}".format(author_name, author_id))
        else:
            await channel.send("Failed: {} is not in the list".format(name))

    async def rename(self, old_name, new_name, channel):
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        if old_name in link_dict:
            link_dict[new_name] = link_dict[old_name]
            del link_dict[old_name]
        else:
            await channel.send("Failed to Rename: {} is not in the list".format(old_name))
            return

        with open(self.link_dict_path, "wb") as f:
            pickle.dump(link_dict, f)
        await channel.send("Successfully Renamed")


