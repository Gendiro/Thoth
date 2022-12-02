import discord
from discord.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def help(self, ctx):
        em = discord.Embed(title="Help",
                           description="Обьяснение всех команд, напишите $help команда для более подробной информации",
                           color=ctx.author.color)

        em.add_field(name="$profile",
                     value="посмотреть свой профиль (Хранители квестов могут смотреть чужие через $profile ник_игрока)")
        em.add_field(name="$get_started", value="Запускает инструкцию по настройке Тота")
        em.add_field(name="$configure_bot", value="Группа команд для настройки бота")
        em.add_field(name="$create_quest", value="Создает квест")
        # TODO сделать чтоб было видно только квест киперу
        em.add_field(name="$confirm_quest", value="Подтверждает сдачу квеста")

        await ctx.send(embed=em)

    @help.command()
    async def configure_bot(self, ctx):
        em = discord.Embed(title="Bot configuration", description="Набор команд используемый для настройки бота")

        em.add_field(name="$configure_bot welcome_channel айди",
                     value="Устанавливает канал с данным айди как приветсвеный канал. " +
                           "Туда будут приходить заготовленные сообщения с приветсвиями новых участников.")
        em.add_field(name="$configure_bot quest_channel айди",
                     value="Устанавливает канал с данным айди как канал для квестов. Там будут создаваться" +
                           " сообщения о квестах. Создавать квесты все ещё можно в любом канале при нужном доступе.")
        em.add_field(name="$configure_bot quest_keeper никнейм",
                     value="(Пере)дает роль хранителя квестов пользователю с данным ник-неймом")

        await ctx.send(embed=em)

    @help.command()
    async def confirm_quest(self, ctx):
        em = discord.Embed(title="Quest confirm", description="Подтверждение что игрок сдал квест")

        em.add_field(name="$configure_bot имя_игрока навазние_квеста",
                     value="Подтверждает что игрок с ником имя_игрок сдал квест название_квеста")

        await ctx.send(embed=em)

    @commands.command(name="get_started")
    async def get_started(self, ctx):
        em = discord.Embed(title="Добро пожаловать в Тот v0.3.1",
                           description="Следуйте этой инструкции для настройки бота под свой сервер!")
        em.add_field(name="1",
                     value="Установите превественный канал командой $configure\_bot welcome\_channel название_канала")
        em.add_field(name="2", value="Установите канал для квестов командой " +
                                     "$configure\_bot quest\_channel название_канала")
        em.add_field(name="3", value="Установите уровни для игроков через команду $configure\_bot levels_config")
        em.add_field(name="4", value="Назначьте хранителя квестов через $configure\_bot give\_keeper имя\_игрока")
        em.add_field(name="5", value="Создавайте свои квесты используя команду $create_quest")
        em.add_field(name="6",
                     value="Принять участие в квесте можно отреагировав ✅ на сообщение с необходимым квестом," +
                           " если мест не осталось то бот отсавит реакцию ❎")
        em.add_field(name="7", value="для отмены участия достаточно убрать свою реацию")
        em.add_field(name="8",
                     value="Пусть выполненный квест подтвердит Хранитель квестов через команду " +
                           "$confirm\_quest имя\_игрока название\_квеста")
        await ctx.send(embed=em)
