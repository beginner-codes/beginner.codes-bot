import dippy.labels
import nextcord

from extensions.kudos.manager import KudosManager
import re
from datetime import timedelta, datetime, timezone
from math import log2
import asyncio
from extensions.shared import message_should_cost_kudos


class GoodReadsSharingExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface
    kudos: KudosManager

    @dippy.Extension.listener("message")
    async def on_message(self, message: nextcord.Message):
        if message_should_cost_kudos(message):
            await self._charge_for_message(message)

    @dippy.Extension.listener("message_edit")
    async def on_message_edit(
        self, old_message: nextcord.Message, message: nextcord.Message
    ):
        if message_should_cost_kudos(message) and not message_should_cost_kudos(
            old_message
        ):
            await self._charge_for_message(message)

    async def _charge_for_message(self, message: nextcord.Message):
        lifetime_kudos = await self.kudos.get_lifetime_kudos(message.author)
        lifetime_limit = 80
        if lifetime_kudos < lifetime_limit:
            await message.delete()
            await message.channel.send(
                f"🛑 {message.author.mention} you must have at least {lifetime_limit} lifetime kudos to share links in "
                f"this channel. You currently only have {lifetime_kudos} lifetime kudos. *Your message has been "
                f"deleted.*",
                delete_after=20,
            )
            return

        kudos = await self.kudos.get_kudos(message.author)
        convert = lambda d: datetime.fromisoformat(d).astimezone(timezone.utc)
        shares = await message.author.get_label("good-reads-shares", [])
        shares = [
            date
            for date in map(convert, shares)
            if message.created_at - date <= timedelta(days=7)
        ]
        cost = round(log2(len(shares) + 1) * 10 + 8)
        nth = self.format_number(len(shares) + 1)
        if kudos < cost:
            await message.delete()
            await message.channel.send(
                f"🛑 {message.author.mention} It would cost you {cost} kudos to share your {nth} link this week. You "
                f"have only {kudos} kudos left. *Your message has been deleted.*",
                delete_after=20,
            )

        confirm_message = await message.reply(
            f"It will cost {cost} kudos to share your {nth} link this week. You have {kudos:,} kudos to spend. Share "
            f"the link? (✅ yes, ❌ no)"
        )
        await confirm_message.add_reaction("✅")
        await confirm_message.add_reaction("❌")

        def check_reactions(payload):
            return (
                payload.message_id == confirm_message.id
                and payload.emoji.name in "✅❌"
                and payload.user_id == message.author.id
            )

        try:
            reaction = await self.client.wait_for(
                "raw_reaction_add", check=check_reactions, timeout=30
            )
        except asyncio.TimeoutError:
            await message.delete()
            await message.channel.send(
                f"🛑 {message.author.mention} your message has been deleted.",
                delete_after=20,
            )
        else:
            if reaction.emoji.name == "✅":
                await self.kudos.take_kudos(
                    message.author,
                    cost,
                    f"{message.author.mention} shared a link in {message.channel.mention}!",
                )
                await message.reply(
                    f"✅ You've paid {cost} kudos to share this link! You have {kudos - cost:,} kudos remaining.",
                    delete_after=10,
                )
                await message.author.set_label(
                    "good-reads-shares",
                    [
                        message.created_at.isoformat(),
                        *map(datetime.isoformat, shares),
                    ],
                )
            else:
                await message.delete()
                await message.channel.send(
                    f"🛑 {message.author.mention} your message has been deleted.",
                    delete_after=20,
                )
        finally:
            await confirm_message.delete()

    def format_number(self, number):
        if number in {11, 12, 13}:
            suffix = "th"

        else:
            suffix = {
                1: "st",
                2: "nd",
                3: "rd",
            }.get(number % 10, "th")

        return f"{number}{suffix}"
