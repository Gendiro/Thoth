from discord import *
from discord.ui import View
from datetime import timedelta


class QuestTypeView(View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.value = None

    @ui.select(
        placeholder="Выберите тип квеста",
        options=[
            SelectOption(label="Дейлик", emoji="🟦"),
            SelectOption(label="Обычный", emoji="🟪"),
            SelectOption(label="Ивент", emoji="🟧")
        ],
    )
    async def select_callback(self, interaction, select):
        if select.values[0] is not None:
            self.value = select.values[0]

    def get_value(self):
        return self.value


class TimeDeltaView(View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.time = None

    @ui.select(
        placeholder="Выберите нужное время",
        options=[
            SelectOption(label="Сразу", emoji="0️⃣"),
            SelectOption(label="Через 1 час", emoji="1️⃣"),
            SelectOption(label="Через 2 часа", emoji="2️⃣"),
            SelectOption(label="Через 3 часа", emoji="3️⃣"),
            SelectOption(label="Через 6 часов", emoji="6️⃣"),
            SelectOption(label="Через 1 день", emoji="1️⃣"),
            SelectOption(label="Через 2 дня", emoji="2️⃣"),
            SelectOption(label="Через 3 дня", emoji="3️⃣"),
            SelectOption(label="Через 1 неделю", emoji="1️⃣"),
            SelectOption(label="Ввести вручную", emoji="#️⃣")
        ]
    )
    async def select_callback(self, interaction, select) -> timedelta or str:
        match select.values[0]:
            case "Сразу":
                self.time = timedelta(microseconds=1)
            case "Через 1 час":
                self.time = timedelta(hours=1)
            case "Через 2 часа":
                self.time = timedelta(hours=2)
            case "Через 3 часа":
                self.time = timedelta(hours=3)
            case "Через 6 часов":
                self.time = timedelta(hours=6)
            case "Через 1 день":
                self.time = timedelta(days=1)
            case "Через 2 дня":
                self.time = timedelta(days=2)
            case "Через 3 дня":
                self.time = timedelta(days=3)
            case "Через 1 неделю":
                self.time = timedelta(days=7)
            case "Ввести вручную":
                self.time = "by hand"

    def get_time_delta(self) -> timedelta or str or None:
        return self.time


class QuestView(View):
    def __init__(self, bot, players_with_quest=None, max_players=0, current_players=None) -> None:
        super().__init__(timeout=None)
        self.max_players = max_players
        if current_players is None:
            self.current_players = max_players
        else:
            self.current_players = current_players
        if players_with_quest is None:
            self.players_with_quest = []
        else:
            self.players_with_quest = players_with_quest
        self.bot = bot

    @ui.button(label="Принять квест", style=ButtonStyle.green, emoji="✅", custom_id="QuestYesButton")
    async def quest_yes_button_callback(self, interaction, button):
        if interaction.user.id in self.players_with_quest:
            await interaction.response.defer()
            return
        count_embed = Embed()
        if self.max_players is not None:
            if not button.disabled:
                self.current_players -= 1
            if self.current_players == 0:
                button.disabled = True
                button.emoji = "❌"
            count_embed.add_field(name="Количество доступных мест", value=f"{self.current_players}/{self.max_players}")
        else:
            count_embed.add_field(name="Количество доступных мест не ограничено", value="")
        self.players_with_quest.append(interaction.user.id)
        print(self.players_with_quest)
        self.bot.dispatch("accepted_quest", interaction.user, interaction.message)
        await interaction.response.edit_message(view=self, embed=count_embed)

    @ui.button(label="Отказаться от квеста", style=ButtonStyle.red, emoji="💀", custom_id="QuestNoButton")
    async def quest_no_button_callback(self, interaction, button):
        if interaction.user.id not in self.players_with_quest:
            await interaction.response.defer()
            return
        if self.children[0].disabled:
            self.children[0].disabled = False
            self.children[0].emoji = "✅"
        self.current_players += 1
        count_embed = Embed()
        count_embed.add_field(name="Количество доступных мест", value=f"{self.current_players}/{self.max_players}")
        self.bot.dispatch("refused_quest", interaction.user, interaction.message)
        self.players_with_quest.remove(interaction.user.id)
        await interaction.response.edit_message(view=self, embed=count_embed)
