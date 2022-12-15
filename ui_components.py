from discord import *
from discord.ui import View
from datetime import timedelta


class QuestTypeView(View):
    def __init__(self) -> None:
        super().__init__()
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
        super().__init__()
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
