import discord
from bs4 import BeautifulSoup
import urllib


mj_dict = {
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
    "4z": "<:5z:690877265751310446>",
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
class Mahjong(object):
    def __init__(self, cmd_keys=["mahjong", "mj"]):
        self.cmd_keys = cmd_keys
        self.dom_list = ["tou", "nan", "sha", "pei", "haku", "hatu", "chun"]

    async def on_command(self, cmd, args, message):
        if cmd in self.cmd_keys:
            if len(args) == 1:
                if args[0] == "nk":
                    # await self.show_random_nanikiru()
                    pass
                else:
                    s = self.hai2emoji(args[0])
                    if s:
                        await message.channel.send(s)
                    else:
                        await message.channel.send("Illegal Input")
            return True
        else:
            return False

    def get_question_page(self, number):
        try:
            with urllib.request.urlopen('https://nnkr.jp/questions/result/' + str(number)) as response:
                text = response.read()
        except Exception as e:
            print(e)

        return text

    def dom2hai(self, span):
        hai_class = tehais[i]['class'][1]
        for i, dom in enumerate(self.dom_list):
            if dom in hai_class:
                return "%dz" % (i + 1)

        if "aka" in hai_class:
            number = "0"
        else:
            number = hai_class[-1]
        if "man" in hai_class:
            _type = "m"
        elif "sou" in hai_class:
            _type = "s"
        elif "pin" in hai_class:
            _type = "p"

        hai = number + _type
        return hai

    def parse_tehai(self, html, to_emoji=True):
        soup = BeautifulSoup(html)
        tehais = soup.select(".tehai li > div > span")
        for i in range(len(tehais)):
            tehais[i] = self.dom2hai(tenhais[i])

        if to_emoji:
            for i in range(len(tehais)):
                tehais[i] = self.hai2emoji(tenhais[i])

    def parse_description(html):
        soup = BeautifulSoup(html)
        title = soup.select(".title > h3")[0].text[:-3]
        content = str(soup.select(".detail > p")[0])
        content = content[3:-4]
        content = re.sub("(<br/>)+", "\n", content)
        return title, content

    def parse_dora(html):
        soup = BeautifulSoup(html)
        dora = soup.select(".dora")[0]
        dora = self.dom2hai(dora)
        dora = self.hai2emoji(dora)
        return dora

    def get_parse_answer_rank(self, number):
        try:
            with urllib.request.urlopen('https://nnkr.jp/answers/result/' + str(number)) as response:
                text = response.read()
                rank_list = text.json()
                new_rank_list = []

        except Exception as e:
            print(e)

    async def show_random_nanikiru_html(self, message):
        number = 10000
        html = self.get_question_page(number)
        tehais = self.parse_tehai(html)
        title, content = self.parse_description(html)
        dora = self.parse_dora(html)
        questioner_answer = self.parse_questioner_answer(html)

        self.get_parse_answer_rank(number)
        questioner, others = self.parse_answer_comment(html)

        self.show_nanikiri(tehais, title, content, dora, answer_ranks, questioner, other_comments, message.channel)

        def show_nanikiru(self, tehais, title, content, dora, answer_ranks, questioner, other_comments, channel):
            s = ""

            s += "\n" + title + " ドラ:" + dora
            s += "\n" + "".join(tehais[:-1])
            s += " " + tehais[-1]
            s += "\n" + content


            channel.send(s)

    def hai2emoji(self, string):
        tiles = []
        tmps = []
        flag = False
        for c in string:
            if "0" <= c <= "9":
                tmps.append(c)
            elif c == "s" or c == "z" or c == "m" or c == "p":
                try:
                    tiles.extend([mj_dict[t + c] for t in tmps])
                except:
                    return None
                flag = True
                tmps = []
            else:
                return None
        if not flag:
            return None
        return "".join(tiles)
