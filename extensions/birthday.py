from asyncio import get_running_loop, sleep
from datetime import datetime

import dippy


class BoostersExtension(dippy.Extension):
    client: dippy.Client

    def __init__(self):
        super().__init__()
        self.when = datetime(2023, 11, 13, 1, 0, 0, 0)
        self.setup()

    def setup(self):
        if datetime.utcnow() > self.when:
            return

        get_running_loop().create_task(self.schedule())

    async def schedule(self):
        duration = (self.when - datetime.utcnow()).total_seconds()
        await sleep(duration)
        await self.celebrate()


    async def celebrate(self):
        channel = self.client.get_channel(644299524151443487)
        await channel.send("https://tenor.com/bBPEM.gif")
        await channel.send(
            "# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨\n"
            "# ✨ Celebrating the server's 3rd year!!! ✨\n"
            "# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨\n"
            "🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈"
            "🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈"
            "🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈"
            "🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈"
            "🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈🎉🥳🎈"
        )
