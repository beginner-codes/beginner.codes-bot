import re

from nextcord import Embed, Message, TextChannel
from extensions.kudos.manager import KudosManager
import dippy.labels


class ChallengesExtension(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager

    DISCUSSION_CHANNEL_ID = 711930226216796170
    WEEKDAY_CHANNEL_ID = 713149192939503678
    SUBMISSIONS_CHANNEL_ID = 713149318797983784

    @dippy.Extension.listener("message")
    async def award_challenge_kudos(self, message: Message):
        if message.channel.id != self.DISCUSSION_CHANNEL_ID:
            return

        if not message.content.startswith("**Challenge"):
            return

        for member in message.mentions:
            await self.kudos.give_kudos(
                member, 4, f"{member.mention} did the weekday challenge!!!"
            )

        if len(message.mentions) > 1:
            await message.channel.send(
                f"Gave all {len(message.mentions)} people who did the challenge 4 kudos!!!"
            )
        else:
            await message.channel.send("Gave 1 person who did the challenge 4 kudos!!!")

    @dippy.Extension.listener("message")
    async def announce_new_challenge(self, message: Message):
        if message.channel.id != self.WEEKDAY_CHANNEL_ID:
            return

        if not message.author.bot:
            return

        if not message.content.startswith("# "):
            return

        *_, title = message.content.split("\n")[0].split(maxsplit=2)
        challenges_channel: TextChannel = self.client.get_channel(
            self.WEEKDAY_CHANNEL_ID
        )
        title = re.sub(r"[^\w\s-]+", "", title)
        await self.client.get_channel(self.SUBMISSIONS_CHANNEL_ID).send(
            embed=Embed(
                title=f"Challenge {title}",
                description=f"Can you solve **Challenge {title}** in {challenges_channel.mention}?",
                color=0x4285F4,
            )
        )
