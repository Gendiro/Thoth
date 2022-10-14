import os
import discord
from discord.ext import commands, tasks
from discord.utils import get
from tinydb import TinyDB, Query
import datetime
import asyncio
from PIL import Image, ImageDraw, ImageFont 

intents = discord.Intents.all()

db = TinyDB('db.json')
dbs = Query()

essential_ids = dict()

TOKEN = db.search(dbs.DISCORD_TOKEN != "")[0]['DISCORD_TOKEN']

bot = commands.Bot(command_prefix='$', intents=intents)
bot.remove_command('help')

@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title="Help", description = "Обьяснение всех команд, напишите $help команда для более подробной информации", color = ctx.author.color)

    em.add_field(name = "$get_started", value = "Запускает инструкцию по настройке Тота")
    em.add_field(name = "$configure_bot", value = "Группа команд для настройки бота")
    em.add_field(name = "$create_quest", value = "Создает квест")

    await ctx.send(embed = em)

@help.command()
async def configure_bot(ctx):
    em = discord.Embed(title = "Bot configuration", description = "Набор команд используемый для настройки бота")
    
    em.add_field(name = "$configure_bot welcome_channel айди", value = "Устанавливает канал с данным айди как приветсвеный канал. Туда будут приходить заготовленные сообщения с приветсвиями новых участников.")
    em.add_field(name = "$configure_bot quest_channel айди", value = "Устанавливает канал с данным айди как канал для квестов. Там будут создаваться сообщения о квестах. Создавать квесты все ещё можно в любом канале при нужном доступе.")

    await ctx.send(embed = em)

last_quest_id = -1
for doc in db.all():
    if doc["type"] == "quest":
        last_quest_id = max(last_quest_id, doc["id"])

def update_essitial_ids():
    for item in iter(db):
        if item["type"] == "id":
            essential_ids[item["name"]] = int(item["value"])

update_essitial_ids()

@bot.command(name="get_started")
async def get_started(ctx):
    em = discord.Embed(title = "Добро пожаловать в Тот v0.1.2", description = "Следуйте этой инструкции для настройки бота под свой сервер!")
    em.add_field(name = "1", value = "Установите превественный канал командой $configure\_bot welcome\_channel ваш\_айди\_канала")
    em.add_field(name = "2", value = "Установите канал для квестов командой $configure\_bot quest\_channel ваш\_айди\_канала")
    em.add_field(name = "3",value = "Создавайте свои квесты используя команду $create_quest")
    await ctx.send(embed = em)

@bot.group()
async def configure_bot(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Такой configure_bot комманды не существует ...')

@configure_bot.command()
async def welcome_channel(ctx, welcome_channel_id):
    db.insert({"type" : "id", "name" : "welcome_channel_id", "value" : int(welcome_channel_id)})
    update_essitial_ids()
    await bot.get_channel(int(welcome_channel_id)).send("Этот канал выбран как вступительный")

@configure_bot.command()
async def quest_channel(ctx, quest_channel_id):
    db.insert({"type" : "id", "name" : "quest_channel_id", "value" : int(quest_channel_id)})
    update_essitial_ids()
    await bot.get_channel(int(quest_channel_id)).send("Этот канал выбран как квестовый")


@bot.command(name="create_quest")
async def create_quest(ctx):
    global last_quest_id
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
        people_limit = "inf"
    else:
        await ctx.send("Ошибка: Число участников не число или слово \"бесконечность\"")
        await ctx.send("Перезапустите создание квеста")       
    await ctx.send("Введите время отправки(В формате год-месяц-день час:минута:секунда с незначащими нулями, пример: 2022-10-13 23:00:04): ")
    send_time = (await bot.wait_for('message', check=check)).content
    await ctx.send("Введите время удаления(В том же формате что и вреия отправки) или слово \"бесконечность\": ")
    delete_time = (await bot.wait_for('message', check=check)).content
    if delete_time == "бесконечность":
        delete_time = None
    await ctx.send("Введите описание задания: ")
    description = (await bot.wait_for('message', check=check)).content 
    last_quest_id += 1
    result_quest = {
        "type" : "quest", 
        "id" : last_quest_id, 
        "title" : title, 
        "reward" : reward, 
        "people_limit" : people_limit,
        "send_time" : send_time,
        "delete_time" : delete_time,
        "description" : description
    }
    db.insert(result_quest)
    await send_quest(ctx, result_quest)

async def send_quest(ctx, quest):
    send_seconds = (datetime.datetime.strptime(quest["send_time"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.now()).total_seconds()
    if quest["delete_time"] != None:
        delete_seconds = (datetime.datetime.strptime(quest["delete_time"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quest["send_time"], "%Y-%m-%d %H:%M:%S")).total_seconds()
    else:
        delete_seconds = None
        quest["delete_time"] = "Постоянное" 
    #await asyncio.sleep(int(send_seconds))
    #await bot.get_channel(essential_ids["quest_channel_id"]).send(f"Название: {quest['title']}", delete_after=delete_seconds)
    #await bot.get_channel(essential_ids["quest_channel_id"]).send(f"Награда: {quest['reward']}", delete_after=delete_seconds)
    #await bot.get_channel(essential_ids["quest_channel_id"]).send(f"Кол-во участников: {quest['people_limit']}", delete_after=delete_seconds)
    #await bot.get_channel(essential_ids["quest_channel_id"]).send(f"Описание: {quest['description']}", delete_after=delete_seconds)
    #await bot.get_channel(essential_ids["quest_channel_id"]).send(f"Будует удалено в: {quest['delete_time']}", delete_after=delete_seconds)
    await create_quest_image(ctx, quest, delete_seconds);

def add_eol(text, n):
    result = ""
    i = 0
    while text != "":
        if i >= len(text) and i < n:
            result += text[:i]
            break
        elif i == n:
            while text[i] != ' ':
                i -= 1
            result += text[:i] + "\n"
            text = text[i+1:]
            i = 0
        i += 1
    return result        

async def create_quest_image(ctx, quest, delete_seconds):
    myFont = ImageFont.truetype("OpenSans-Regular.ttf", 100)
    img = Image.open('quest_template.png')
    imgDraw = ImageDraw.Draw(img)
    imgDraw.text((600, 400), quest["title"], fill=(244, 233, 205), font = myFont)
    imgDraw.text((600, 850), add_eol(quest["description"], 46), fill=(244, 233, 205), spacing = 10,font = myFont)
    if quest["people_limit"] == "inf":
        imgDraw.text((550, 1850), "Для всех", fill=(244, 233, 205), font = ImageFont.truetype("OpenSans-Regular.ttf", 85))
    else:
        imgDraw.text((550, 1850), f"{quest['people_limit']}/{quest['people_limit']} игроков", fill=(244, 233, 205), font = ImageFont.truetype("OpenSans-Regular.ttf", 85))
    imgDraw.text((1400, 1850), f"{quest['reward']} опыта", fill=(244, 233, 205), font = myFont)
    if quest["delete_time"] == "Постоянное":
        imgDraw.text((2400, 1850), f"{quest['delete_time']}", fill=(244, 233, 205), font = ImageFont.truetype("OpenSans-Regular.ttf", 85))
    else:
        quest_dt = datetime.datetime.strptime(quest["delete_time"], "%Y-%m-%d %H:%M:%S")
        if(datetime.datetime.now().day == quest_dt.day):
            imgDraw.text((2400, 1850), quest_dt.strftime("До %H:%M"), fill=(244, 233, 205), font = ImageFont.truetype("OpenSans-Regular.ttf", 85))
        else:
            imgDraw.text((2400, 1850), quest_dt.strftime("До %H:%M %d.%m"), fill=(244, 233, 205), font = ImageFont.truetype("OpenSans-Regular.ttf", 85))
    img.save(f"quest_{last_quest_id}.png")
    img = discord.File(f"quest_{last_quest_id}.png")
    await bot.get_channel(essential_ids["quest_channel_id"]).send(file=img, delete_after=delete_seconds)
    os.remove(f"quest_{last_quest_id}.png")

@bot.event
async def on_member_join(member):
    if "welcome_channel_id" in essential_ids:
        await bot.get_channel(essential_ids["welcome_channel_id"]).send(f'Приветствуем <@{member.id}>')

@bot.command(name="check_db")
async def check_db(ctx):
  await ctx.send(essential_ids)

bot.run(TOKEN)