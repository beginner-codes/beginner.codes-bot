from asyncio import get_running_loop, sleep
from datetime import datetime

import dippy


class BoostersExtension(dippy.Extension):
    client: dippy.Client

    def __init__(self):
        super().__init__()
        now = datetime.utcnow()
        self.when = datetime(now.year, 11, 13, 1, 0, 0, 0)
        self.setup()

    def update_next_birthday(self):
        if datetime.utcnow() > self.when:
            self.when = self.when.replace(year=self.when.year + 1)

    def how_many_years_old(self) -> str:
        return self.ordinal(self.when.year - 2020)

    def ordinal(self, n: int):
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return f"{n}{suffix}"

    def setup(self):
        self.update_next_birthday()
        get_running_loop().create_task(self.schedule())

    async def schedule(self):
        duration = (self.when - datetime.utcnow()).total_seconds()
        await sleep(duration)
        await self.celebrate()
        self.setup()

    def prepare_celebration_message(self) -> str:
        announcement_line = f"#  Celebrating the server's {self.how_many_years_old()} year!!\n"

        # len(announcement_line) / 2 due to the sparkles having about the width of two characters
        very_sparkly_decoration = "# " + "✨"* int(len(announcement_line) /2 - 1) + "\n"

        very_happy_decoration = "🎉🥳🎈" * 15 + "\n"
        return f"{very_sparkly_decoration}{announcement_line}{very_sparkly_decoration}{very_happy_decoration * 3}"

    async def celebrate(self):
        channel = self.client.get_channel(644299524151443487)
        await channel.send("https://tenor.com/bBPEM.gif")
        await channel.send(
            self.prepare_celebration_message()
        )
