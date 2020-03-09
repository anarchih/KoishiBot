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


PATIENT_TIME = 120
RECOVER_TIME = 120

def delete_image(folder, name):
    files = os.listdir(folder)
    for f in files:
        if name == f[:-4]:
            os.remove(os.path.join(folder, f))
            break


class Koishi(object):
    def __init__(self):
        self.mention_context = KoishiMentionContext()
        self.jyanken = KoishiJyanken()
        self.test_game = KoishiTestGame()
        self.file_manager = KoishiFileManager()

class KoishiFileManager(object):
    def __init__(self):
        self.link_dict_path = "link_dict.pickle"
        self.list_keywords = ["list", "ls", "l"]
        self.rlist_keywords = ["rlist", "rls", "rl"]
        self.save_keywords = ["save", "sv", "s"]
        self.delete_keywords = ["delete", "del", "d"]
        self.keywords = sum([
            self.list_keywords,
            self.rlist_keywords,
            self.save_keywords,
            self.delete_keywords
        ], [])

        if not os.path.exists(self.link_dict_path):
            with open(self.link_dict_path, "wb") as f:
                pickle.dump({}, f)

        self.list_message = None
        self.list_page = None
        self.list_regex = ""
        self.page_size = 20
        self.reaction_list = ["⬅️", "➡️"]
        self.display_list = []

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
        else:
            await self.show(cmd, message.channel)

    def save_attachment_link(self, name, attachment):
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
            link_dict[name] = (url, filename, file_ext)
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
        elif len(name) > 100:
            if send_error:
                await channel.send("Failed to Save: Length of [Name] should not be > 100")
            return False
        return True

    async def save_url(self, name, url, message):
        name = name.lower()
        channel = message.channel
        if not await self.is_name_valid(name, send_error=True, channel=channel):
            return
        elif not is_url(url):
            await channel.send("Failed to Save: It's not a Legal URL")
        elif len(url) > 1000:
            await channel.send("Failed to Save: Length of Link should not be > 1000")
        else:
            with open(self.link_dict_path, 'rb') as f:
                link_dict = pickle.load(f)
            link_dict[name] = (url, "", "")
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
                ret = self.save_attachment_link(name, message.attachments[0])
            else:
                await channel.send("Failed to Save: No Attachment")
                return

            if ret == -1:
                await channel.send("Failed to Save: Unknown File Type (jpg, png & gif only)")
            elif ret == 0:
                await channel.send("Successfully Saved")
        except Exception as e:
            print(e)
            await channel.send("Failed to Save: Unknown Error")

    async def show_list(self, display_list, channel=None):
        display_list += [""] * (self.page_size - len(display_list))
        s = "Existing Files:\n- "
        s += "\n- ".join(display_list)
        if channel:
            return await channel.send(content=s)
        elif self.list_message:
            return await self.list_message.edit(content=s)
        else:
            return None

    async def _list(self, regex, channel):
        with open(self.link_dict_path, "rb") as f:
            display_list = list(pickle.load(f))
        if regex:
            self.list_regex = regex
            display_list = [name for name in display_list if re.search(regex, name)]
        else:
            self.list_regex = ""

        display_list.sort()

        message = await self.show_list(display_list[:self.page_size], channel)

        if not message:
            return

        for reaction in self.reaction_list:
            await message.add_reaction(reaction)

        self.display_list = display_list
        self.list_page = 0
        self.list_message = message

    async def change_list_page(self, reaction):
        if reaction == self.reaction_list[0]:
            self.list_page -= 1
        elif reaction == self.reaction_list[1]:
            self.list_page += 1
        else:
            return

        display_list = self.display_list
        total_pages = math.ceil(len(display_list) / self.page_size)
        try:
            self.list_page %= total_pages
        except:
            return

        #
        start = self.list_page * self.page_size
        end = start + self.page_size
        display_list = display_list[start: end]
        await self.show_list(display_list)

    async def delete(self, name, channel):
        name = name.lower()
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        if name in link_dict:
            del link_dict[name]

        else:
            await channel.send("Failed to Delete: [Name] is Not in the List")
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
                    await channel.send("Link is Lost")
        else:
            await channel.send("Failed: {} is not in the List".format(name))


"""
class KoishiTestGame(object):
    def __init__(self):
        self.game_message = None
        self.map_dict = {
            0: "⬛",
            1: "🔺",
            2: "◽"
        }
        #self.reaction_list = ["⬅️", "⬇️", "⬆️", "➡️"]
        self.reaction_list = ["⬅️", "➡️"]

    async def start(self, channel):
        self.generate_map()
        await self.send_map(channel)
        await self.add_reactions()

    async def send_map(self, channel):
        map_str = self.map2str()
        self.game_message = await channel.send(map_str)

    async def update_map(self):
        map_str = self.map2str()
        await self.game_message.edit(content=map_str)

    async def add_reactions(self):
        message = self.game_message
        for reaction in self.reaction_list:
            await message.add_reaction(reaction)

    def generate_map(self):
        self._map = np.zeros((9, 9))
        self._map[8, 4] = 1
        self.pos_y, self.pos_x = 8, 4

    def map2str(self):
        map_list = self._map.tolist()
        height, width = self._map.shape
        map_str = ""
        for i in range(height):
            for j in range(width):
                key = map_list[i][j]
                map_list[i][j] = self.map_dict[key]
            map_str += "".join(map_list[i]) + "\n"
        return map_str

    async def move(self, reaction):
        self._map[self.pos_y][self.pos_x] = 0
        print(reaction, self.reaction_list[0])
        if reaction == self.reaction_list[0]:
            self.pos_x = (self.pos_x - 1) % 9
        #elif reaction == self.reaction_list[1]:
        #    self.pos_y = (self.pos_y + 1) % 9
        #elif reaction == self.reaction_list[2]:
        #    self.pos_y = (self.pos_y - 1) % 9
        elif reaction == self.reaction_list[3]:
            self.pos_x = (self.pos_x + 1) % 9

        self._map[self.pos_y][self.pos_x] = 1

        await self.update_map()
"""
class KoishiTestGame(object):
    def __init__(self):
        self.game_message = None
        self.status = 0
        self.score = 0
        self.map_dict = {
            0: "⬛",
            1: "🔺",
            2: "◽",
            3: "❌"
        }
        self.reaction_list = ["⬅️", "⏸️", "➡️"]

    async def start(self, channel):
        self.generate_map()
        await self.send_map(channel)
        await self.add_reactions()
        self.status = 1
        self.score = 0

    async def send_map(self, channel, postfix="."):
        map_str = "Score: " + str(self.score) + "\n"
        map_str += self.map2str()
        map_str += "\n\n\n\n" + postfix
        self.game_message = await channel.send(map_str)

    async def update_map(self, postfix="."):
        map_str = "Score: " + str(self.score) + "\n"
        map_str += self.map2str()
        map_str += "\n\n\n\n" + postfix
        await self.game_message.edit(content=map_str)

    async def add_reactions(self):
        message = self.game_message
        for reaction in self.reaction_list:
            await message.add_reaction(reaction)

    def generate_map(self):
        self._map = np.zeros((9, 9))
        self._map[8, 4] = 1
        self.pos_y, self.pos_x = 8, 4

    def map2str(self):
        map_list = self._map.tolist()
        height, width = self._map.shape
        map_str = ""
        for i in range(height):
            for j in range(width):
                key = map_list[i][j]
                map_list[i][j] = self.map_dict[key]
            map_str += "".join(map_list[i]) + "\n"
        return map_str

    async def send_lose_info(self, name):
        self.status = 0
        await self.update_map(postfix=name + " Lose")

    async def move(self, user, reaction):
        if not self.status:
            return

        # Character Update
        if reaction == self.reaction_list[0]:
            self.pos_x = (self.pos_x - 1) % 9
        elif reaction == self.reaction_list[1]:
            pass
        elif reaction == self.reaction_list[2]:
            self.pos_x = (self.pos_x + 1) % 9
        else:
            return

        # Environment Update
        self._map = np.roll(self._map, shift=1, axis=0)
        self._map[0] = 0
        r = random.randint(0, 1)
        if r:
            r_pos = random.randint(0, self._map.shape[1] - 1)
            self._map[0, r_pos] = 2

        self.score += 1

        if self._map[self.pos_y][self.pos_x] == 0:
            self._map[self.pos_y][self.pos_x] = 1
            await self.update_map()
        else:
            self._map[self.pos_y][self.pos_x] = 3
            self.status = 0
            await self.send_lose_info(user.name)



class KoishiStatusManager(object):
    def __init__(self, data_file="status"):
        pass

    def update_status():
        pass


class KoishiStatus(object):
    def __init__(self):
        self.happiness = 0
        self.favorability = 0

class KoishiJyanken(object):
    def __init__(self):
        self.act_dict = {
            0: "✌️",
            1: "✊",
            2: "🖐️",
            3: "🖕",
        }
        self.reversed_act_dict = {v: k for k, v in self.act_dict.items()}
        self.refused_time = 0

    async def do_jyanken(self, channel, other_act_key):
        try:
            other_act = self.reversed_act_dict[other_act_key]

            if other_act == 3:
                await send_image(channel, "displeasing.png")
                self.refused_time = time.time()
                return

            if time.time() - self.refused_time < 60:
                await send_image(channel, "annoy.png")
                return

            act = random.randint(0, 2)
            react = random.randint(0, 1)
            # Middle Finger Case
            if (act - other_act) % 3 == 0:
                if react: await send_image(channel, "excited.png", self.act_dict[act])
                else: await send_image(channel, "facepalm.png", self.act_dict[act])
            elif (act - other_act) % 3 == 1:
                if react: await send_image(channel, "ya.png", self.act_dict[act])
                else: await send_image(channel, "ridicule.png", self.act_dict[act])
            else:
                if react: await send_image(channel, "angry.png", self.act_dict[act])
                else: await send_image(channel, "cry.png", self.act_dict[act])
        except Exception as e:
            print(e)

class KoishiMentionContext(object):
    def __init__(self, state=None):
        self.time_list = [0, 0, 0]
        if not state:
            self.transition_to(NormalState())
        else:
            self.transition_to(state)

    def update_time_list(self):
        mentioned_time = time.time()
        self.time_list.append(mentioned_time)
        self.time_list = self.time_list[1:]

    def clear_time_list_except_latest(self):
        self.time_list = [0, 0, self.time_list[-1]]

    def clear_time_list(self):
        self.time_list = [0, 0, 0]

    def transition_to(self, state):
        self._state = state
        self._state.context = self

    async def mentioned(self, channel):
        await self._state.send_action(channel)

class State(object):
    def send_reaction(self):
        pass
        #await send_image()

class NormalState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[0] <= PATIENT_TIME:
            self.context.transition_to(AnnoyState())
            self.context.clear_time_list_except_latest()
        await send_image(channel, "happy.png")

class AnnoyState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[-2] >= RECOVER_TIME:
            self.context.clear_time_list()
            self.context.transition_to(NormalState())
            await self.context.mentioned(channel)
            return

        elif time_list[-1] - time_list[0] <= PATIENT_TIME:
            self.context.clear_time_list_except_latest()
            self.context.transition_to(AngryState())

        await send_image(channel, "annoy.png")

class AngryState(object):
    async def send_action(self, channel):
        self.context.update_time_list()
        time_list = self.context.time_list

        if time_list[-1] - time_list[-2] >= RECOVER_TIME:
            self.context.clear_time_list()
            self.context.transition_to(NormalState())
            await self.context.mentioned(channel)
            return

        await send_image(channel, "angry.png")

