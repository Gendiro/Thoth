import math
import os
import discord
from discord.ext import commands
from tinydb import TinyDB, Query
import datetime
from PIL import Image, ImageDraw, ImageFont
from cogs.help import Helper
from table2ascii import table2ascii, PresetStyle

# Creates a bot (All intents just in case, help removed to be replaced by custom one)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)
bot.remove_command('help')
# The database
db = TinyDB('db.json')
# The token to run the bot
TOKEN = db.search(Query().DISCORD_TOKEN != "")[0]['DISCORD_TOKEN']
# Channels ids
welcome_channel_id = 0
if db.search(Query().type == "welcome_channel_id"):
    welcome_channel_id = db.search(Query().type == "welcome_channel_id")[0]["value"]
quest_channel_id = 0
if db.search(Query().type == "quest_channel_id"):
    quest_channel_id = db.search(Query().type == "quest_channel_id")[0]["value"]
titles = [
    "Старейшина",
    "Возносящийся в старейшины",
    "Администратор",
    "Премьер-секретарь",
    "Советник",
    "Посол",
    "Бригадир",
    "Инженер",
    "Рейнджер",
    "Рекрут",
    "Кочевник"
][::-1]


# a checker for @commands.check to make command only accessible to quest keepers
async def quest_keeper_level(ctx):
    keeper_role = discord.utils.get(ctx.guild.roles, name="Quest keeper")
    if keeper_role in ctx.author.roles:
        return True
    else:
        await ctx.send("Извините, это команда только для квест киперов")
        return False


# loading additional modules in separate files
@bot.event
async def on_ready():
    await bot.add_cog(Helper(bot))


# Simply adds empty profile with players id into db
def add_player_to_db(player_id):
    if not db.search(Query().id == player_id):
        db.insert({
            "type": "player",
            "id": player_id,
            "level": 0,
            "exp": 0,
            "current_quests": []
        })


# triggers only when bot joins the server, imports all people in there into db (do this in add_player probably)
@bot.event
async def on_guild_join(guild):
    for member in guild.members:
        add_player_to_db(member.id)


# added it just in case someone logins in while the bot is offline
@bot.command(name="add_everyone")
@commands.check(quest_keeper_level)
async def add_every_user(ctx):
    for member in ctx.guild.members:
        if member.id != bot.application_id:
            add_player_to_db(member.id)
            stranger_role = discord.utils.get(member.guild.roles, name=titles[0])
            await member.add_roles(stranger_role)


async def give_player_xp(ctx, player, exp):
    player_profile = db.search(Query().id == player.id)[0]
    player_profile["exp"] += exp
    while player_profile["exp"] >= player_profile["level"] * 5 + 5:
        player_profile["exp"] -= player_profile["level"] * 5 + 5
        player_profile["level"] += 1
        if math.floor((player_profile["level"] - 1) / 10) != math.floor(player_profile["level"] / 10):
            old_title_id = math.floor((player_profile["level"] - 1) / 10)
            new_title_id = math.floor(player_profile["level"] / 10)
            old_title = discord.utils.get(ctx.guild.roles, name=titles[old_title_id])
            new_title = discord.utils.get(ctx.guild.roles, name=titles[new_title_id])
            if old_title is None:
                old_title = await ctx.guild.create_role(name=titles[old_title_id], hoist=True)
            if new_title is None:
                new_title = await ctx.guild.create_role(name=titles[new_title_id], hoist=True)
            await player.remove_roles(old_title)
            await player.add_roles(new_title)

    db.update({"exp": player_profile["exp"], "level": player_profile["level"]}, Query().id == player.id)


@bot.command(name="give_exp")
@commands.check(quest_keeper_level)
async def give_exp(ctx, player_name, exp):
    player = discord.utils.get(ctx.guild.members, name=player_name)
    await give_player_xp(ctx, player, int(exp))


# Greats new players and adds them to db
@bot.event
async def on_member_join(member):
    if welcome_channel_id:
        await bot.get_channel(welcome_channel_id).send(f'Приветствуем <@{member.id}>')
    stranger_role = discord.utils.get(member.guild.roles, name=titles[0])
    await member.add_roles(stranger_role)
    add_player_to_db(member.id)


# configure_bot group of commands
@bot.group(name="configure_bot")
@commands.check(quest_keeper_level)
async def configure_bot(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Такой configure_bot комманды не существует ...')


@configure_bot.command()
@commands.check(quest_keeper_level)
async def welcome_channel(ctx, welcome_channel_name):
    global welcome_channel_id
    channel = discord.utils.get(ctx.guild.channels, name=welcome_channel_name)
    welcome_channel_id = channel.id
    db.insert({"type": "welcome_channel_id", "value": int(welcome_channel_id)})
    if quest_channel_id:
        await bot.get_channel(int(welcome_channel_id)).send("Этот канал выбран как вступительный")


@configure_bot.command()
@commands.check(quest_keeper_level)
async def quest_channel(ctx, quest_channel_name):
    global quest_channel_id
    channel = discord.utils.get(ctx.guild.channels, name=quest_channel_name)
    quest_channel_id = channel.id
    db.insert({"type": "quest_channel_id", "value": int(quest_channel_id)})
    await bot.get_channel(int(quest_channel_id)).send("Этот канал выбран как квестовый")


@bot.command(name="create_quest")
@commands.check(quest_keeper_level)
async def create_quest(ctx):
    if not quest_channel_id:
        await ctx.send("Канал для квестов ещё не был выбран")
        return

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send("Введите название квеста: ")
    title = (await bot.wait_for('message', check=check)).content
    await ctx.send("Введите награду за квест: ")
    reward = (await bot.wait_for('message', check=check)).content
    if not reward.isnumeric():
        await ctx.send("Ошибка: Опыт должен быть введен числом без допольнительных знаков")
        await ctx.send("Перезапустите создание квеста")
    reward = int(reward)
    await ctx.send("Введите максимальное число участников(число или слово \"бесконечность\"): ")
    people_limit = (await bot.wait_for('message', check=check)).content
    if people_limit.isnumeric():
        people_limit = int(people_limit)
    elif people_limit == "бесконечность":
        people_limit = None
    else:
        await ctx.send("Ошибка: Число участников не число или слово \"бесконечность\"")
        await ctx.send("Перезапустите создание квеста")
    await ctx.send(
        "Введите время отправки(В формате год-месяц-день час:минута:секунда с " +
        "незначащими нулями, пример: 2022-10-13 23:00:04): ")
    send_time = (await bot.wait_for('message', check=check)).content
    await ctx.send("Введите время удаления(В том же формате что и вреия отправки) или слово \"бесконечность\": ")
    delete_time = (await bot.wait_for('message', check=check)).content
    if delete_time == "бесконечность":
        delete_time = None
    await ctx.send("Введите описание задания: ")
    description = (await bot.wait_for('message', check=check)).content
    result_quest = {
        "type": "quest",
        "title": title,
        "reward": reward,
        "people_limit": people_limit,
        "send_time": send_time,
        "delete_time": delete_time,
        "description": description
    }
    await send_quest(ctx, result_quest)


async def send_quest(ctx, quest):
    if quest["delete_time"] is not None:
        delete_seconds = (
                datetime.datetime.strptime(quest["delete_time"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(
                                            quest["send_time"], "%Y-%m-%d %H:%M:%S")).total_seconds()
    else:
        delete_seconds = None
        quest["delete_time"] = "Постоянное"
    await create_quest_image(ctx, quest, delete_seconds)


def add_eol(text, n):
    result = ""
    i = 0
    while text != "":
        if len(text) <= i < n:
            result += text[:i]
            break
        elif i == n:
            while text[i] != ' ':
                i -= 1
            result += text[:i] + "\n"
            text = text[i + 1:]
            i = 0
        i += 1
    return result


async def create_quest_image(ctx, quest, delete_seconds):
    # printing only to turn off the "unused parameter warning"
    print(ctx.author)
    my_font = ImageFont.truetype("OpenSans-Regular.ttf", 100)
    img = Image.open('quest_template.png')
    img_draw = ImageDraw.Draw(img)
    img_draw.text((600, 400), quest["title"], fill=(244, 233, 205), font=my_font)
    img_draw.text((600, 850), add_eol(quest["description"], 46), fill=(244, 233, 205), spacing=10, font=my_font)
    if quest["people_limit"] is None:
        img_draw.text((550, 1850), "Для всех", fill=(244, 233, 205),
                      font=ImageFont.truetype("OpenSans-Regular.ttf", 85))
    else:
        img_draw.text((550, 1850), f"{quest['people_limit']}/{quest['people_limit']} игроков", fill=(244, 233, 205),
                      font=ImageFont.truetype("OpenSans-Regular.ttf", 85))
    img_draw.text((1400, 1850), f"{quest['reward']} опыта", fill=(244, 233, 205), font=my_font)
    if quest["delete_time"] == "Постоянное":
        img_draw.text((2400, 1850), f"{quest['delete_time']}", fill=(244, 233, 205),
                      font=ImageFont.truetype("OpenSans-Regular.ttf", 85))
    else:
        quest_dt = datetime.datetime.strptime(quest["delete_time"], "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now().day == quest_dt.day:
            img_draw.text((2400, 1850), quest_dt.strftime("До %H:%M"), fill=(244, 233, 205),
                          font=ImageFont.truetype("OpenSans-Regular.ttf", 85))
        else:
            img_draw.text((2400, 1850), quest_dt.strftime("До %H:%M %d.%m"), fill=(244, 233, 205),
                          font=ImageFont.truetype("OpenSans-Regular.ttf", 85))
    last_quest_id = 0
    while os.path.isfile(f"quest_{last_quest_id}.png"):
        last_quest_id += 1
    img.save(f"quest_{last_quest_id}.png")
    img = discord.File(f"quest_{last_quest_id}.png")
    message = await bot.get_channel(quest_channel_id).send(file=img, delete_after=delete_seconds)
    quest["id"] = message.id
    db.insert(quest)
    os.remove(f"quest_{last_quest_id}.png")


# noinspection PyTypeChecker
@bot.command(name="confirm_quest")
@commands.check(quest_keeper_level)
async def confirm_quest(ctx, player_name, *, quest_title):
    keeper_role = discord.utils.get(ctx.guild.roles, name="Quest keeper")
    if not (keeper_role in ctx.author.roles):
        await ctx.send("Sorry, this command is only for keepers")
        return
    player = discord.utils.get(ctx.guild.members, name=player_name)
    if player is None:
        await ctx.send("Sorry, no such player is found")
        return
    # noinspection PyTypeChecker
    player_profile = db.search(Query().id == player.id)[0]
    quests = db.search(Query().title == quest_title)
    if not quests:
        await ctx.send("Sorry, but there is no such quest")
        return
    quest_data = quests[0]
    # No need to remove the quest here, we do it in the on_raw_reaction_remove anyway
    await give_player_xp(ctx, player, quest_data["reward"])
    quest_channel_temp = await bot.fetch_channel(quest_channel_id)
    message = await quest_channel_temp.fetch_message(quest_data["id"])
    player_member = await bot.fetch_user(player_profile["id"])
    await message.remove_reaction("✅", player_member)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.application_id:
        return
    if payload.emoji.name == "✅" and (db.search(Query().id == payload.message_id)):
        player = db.search(Query().id == payload.user_id)[0]
        quest_data = db.search(Query().id == payload.message_id)[0]
        if quest_data["people_limit"] is not None:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if quest_data["people_limit"] == 0:
                await message.remove_reaction("✅", payload.member)
            else:
                db.remove(Query().id == payload.message_id)
                quest_data["people_limit"] -= 1
                db.insert(quest_data)
                if quest_data["people_limit"] == 0:
                    await message.add_reaction("❎")
        player["current_quests"].append(payload.message_id)
        db.remove(Query().id == payload.user_id)
        db.insert(player)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name == "✅" and (db.search(Query().id == payload.message_id)):
        player = db.search(Query().id == payload.user_id)[0]
        quest_data = db.search(Query().id == payload.message_id)[0]
        if quest_data["people_limit"] is not None:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            db.remove(Query().id == payload.message_id)
            quest_data["people_limit"] += 1
            db.insert(quest_data)
            bot_user = await bot.fetch_user(1001949200600272896)
            await message.remove_reaction("❎", bot_user)
        player["current_quests"].remove(payload.message_id)
        db.remove(Query().id == payload.user_id)
        db.insert(player)


def get_board():
    players = db.search(Query().type == "player")
    return sorted(players, key=lambda d: d['exp'] + (20 + 5 * (d['level'] - 2)) / 2 * (d['level'] - 1) + 5)[::-1]


def calculate_player_rank(player_id):
    board = get_board()
    for i in range(len(board)):
        if board[i]["id"] == player_id:
            return max(0, i - 2)


@bot.command(name="leaderboard")
async def leaderboard(ctx):
    board = get_board()
    prepared_board = []
    for i in range(3, min(len(board), 13)):
        member = await ctx.guild.fetch_member(board[i]["id"])
        if member.nick:
            name = member.nick
        else:
            player = await bot.fetch_user(board[i]["id"])
            name = player.name
        prepared_board.append([i - 2, name, board[i]['exp'], board[i]['level']])
    output = table2ascii(header=["Rank", "Name", "Level", "Exp"], body=prepared_board, style=PresetStyle.thin_compact)
    await ctx.send(f"```\n{output}\n```")


@bot.command(name="profile")
async def profile(ctx, other_name=""):
    author = ctx.author
    if other_name != "":
        keeper_role = discord.utils.get(ctx.guild.roles, name="Quest keeper")
        if not (keeper_role in ctx.author.roles):
            await ctx.send("Sorry, only keeper can see other players profile")
            return
        player = discord.utils.get(ctx.guild.members, name=other_name)
        if player is None:
            await ctx.send("Sorry, no such player is found")
            return
        author = db.search(Query().id == player.id)[0]
        if author is None:
            await ctx.send("profile of this user is not created yet")
            return
        author_name = other_name
        author_avatar = player.avatar
    else:
        for document in db.all():
            if document["type"] == "player" and document["id"] == ctx.author.id:
                author = document
        if author is None:
            add_player_to_db(ctx.author.id)
            await profile(ctx)
            return
        author_name = ctx.author.name
        author_avatar = ctx.author.avatar
    embed = discord.Embed()
    embed.set_thumbnail(url=author_avatar)
    embed.add_field(name="Пользователь: ", value=f"{author_name}")
    embed.add_field(name="Уровень: ", value=f"{author['level']}")
    embed.add_field(name="Звание: ", value=f"{titles[math.floor(author['level']/10)]}")
    embed.add_field(name="Место в рейтинге: ", value=f"{calculate_player_rank(author['id'])}")
    embed.add_field(name="Опыт: ", value=f"{author['exp']}/{author['level'] * 5 + 5}")
    s = "Нет активных заданий"
    for quest_id in author["current_quests"]:
        if s == "Нет активных заданий":
            s = ""
        quest_title = db.search(Query().id == quest_id)[0]["title"]
        s += f"{quest_title}\n"
    embed.add_field(name="Активные задания: ", value=s)
    await ctx.send(embed=embed)


bot.run(TOKEN)
