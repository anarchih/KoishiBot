import discord
import time
from utils import send_image
import random
import numpy as np
import urllib
import imghdr
import os
import pickle


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
        self.image_manager = KoishiImageManager()

class KoishiImageManager(object):
    def __init__(self):
        self.link_dict_path = "link_dict.pickle"
        self.keywords = ["list", "save", "delete"]
        if not os.path.exists(self.link_dict_path):
            with open(self.link_dict_path, "wb") as f:
                pickle.dump({}, f)

    async def run(self, sub_cmd_list, message):
        cmd = sub_cmd_list[0].lower()
        if cmd == "list":
            await self._list(message.channel)
        elif cmd == "save":
            if len(sub_cmd_list) == 2:
                await self.save(sub_cmd_list[1].lower(), message)
        elif cmd == "delete":
            if len(sub_cmd_list) == 2:
                await self.delete(sub_cmd_list[1].lower())
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

    async def save(self, name, message):
        name = name.lower()
        channel = message.channel
        if name in self.keywords:
            await channel.send("Failed to Save: Do not use the keywords.")
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

    async def _list(self, channel):
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)
        files = list(link_dict.keys())
        files.sort()
        s = "Existing Files:\n- "
        s += "\n- ".join(files)

        await channel.send(s)

    async def delete(self, name):
        name = name.lower()
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        if name in link_dict:
            del link_dict[name]

        with open(self.link_dict_path, "rb") as f:
            pickle.dump(link_dict, f)

    async def show(self, name, channel):
        with open(self.link_dict_path, "rb") as f:
            link_dict = pickle.load(f)

        name = name.lower()
        if name in link_dict:
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
            2: "✋",
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

