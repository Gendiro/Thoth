import discord
from discord.ext import commands, tasks
from tinydb import TinyDB, Query
import random
from datetime import datetime


# a checker for @commands.check to make command only accessible to quest keepers
async def quest_keeper_level(ctx):
    keeper_role = discord.utils.get(ctx.guild.roles, name="Quest keeper")
    if keeper_role in ctx.author.roles:
        return True
    else:
        await ctx.send("Извините, это команда только для квест киперов")
        return False


class Dailies(commands.Cog):
    def __init__(self, bot, db: TinyDB, create_quest_image) -> None:
        self.bot = bot
        self.db = db
        self.create_quest_image = create_quest_image
        if not db.search(Query().type == "dailies"):
            self.dailies = dict()
            self.exp = 0
            self.count = 0
            self.last_time = ""
            db.insert({"type": "dailies", "values": dict(), "exp": 0, "count": 0, "last_time": ""})
        else:
            dailies_info = db.search(Query().type == "dailies")[0]
            self.dailies = dailies_info["values"]
            self.exp = dailies_info["exp"]
            self.count = dailies_info["count"]
            self.last_time = dailies_info["last_time"]
        self.send_dailies.start()

    @commands.command()
    @commands.check(quest_keeper_level)
    async def see_dailies(self, ctx) -> None:
        result_string = ""
        for daily in self.dailies.keys():
            result_string += daily + "\n"
        await ctx.send(f"```\n{result_string}\n```")
        await ctx.message.delete()

    @commands.command()
    @commands.check(quest_keeper_level)
    async def add_daily(self, ctx) -> None:
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        explanation_message = await ctx.send("Введите название и следующим сообщением описание нового дейлика")
        title_message = await self.bot.wait_for('message', check=check)
        await title_message.delete()
        description_message = await self.bot.wait_for('message', check=check)
        await description_message.delete()
        self.dailies[title_message.content] = description_message.content
        self.db.update({"values": self.dailies}, Query().type == "dailies")
        await explanation_message.delete()
        await ctx.message.delete()

    @commands.command()
    @commands.check(quest_keeper_level)
    async def delete_daily(self, ctx) -> None:
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        explanation_message = await ctx.send("Введите название квеста которого нужно удалить из списка дейликов")
        response_message = await self.bot.wait_for('message', check=check)
        if response_message.content in self.dailies.keys():
            self.dailies.pop(response_message.content)
            self.db.update({"values": self.dailies}, Query().type == "dailies")
        else:
            await ctx.send("Извините, такого дейлика не существует")
        await response_message.delete()
        await explanation_message.delete()
        await ctx.message.delete()

    @commands.command()
    @commands.check(quest_keeper_level)
    async def dailies_set_exp(self, ctx, exp):
        self.exp = exp
        self.db.update({"exp": int(exp)}, Query().type == "dailies")

    @commands.command()
    @commands.check(quest_keeper_level)
    async def dailies_set_count(self, ctx, count):
        self.count = count
        self.db.update({"count": int(count)}, Query().type == "dailies")

    @tasks.loop(minutes=5.0)
    async def send_dailies(self):
        if datetime.today().strftime("%Y-%m-%d") == self.last_time:
            return
        self.last_time = datetime.today().strftime("%Y-%m-%d")
        self.db.update({"last_time": self.last_time}, Query().type == "dailies")
        delete_time = self.last_time + " 23:59:59"
        delete_seconds = (datetime.strptime(delete_time, "%Y-%m-%d %H:%M:%S")
                          - datetime.now()).total_seconds()
        quests = list(self.dailies.keys())
        random.shuffle(quests)
        for quest in quests[:self.count]:
            result_quest = {
                "type": "quest",
                "title": quest,
                "reward": self.exp,
                "people_limit": None,
                "send_time": None,
                "delete_time": delete_time,
                "description": self.dailies[quest]
            }
            await self.create_quest_image(result_quest, delete_seconds, "Дейлик")

    @send_dailies.before_loop
    async def before_send_dailies(self):
        await self.bot.wait_until_ready()
