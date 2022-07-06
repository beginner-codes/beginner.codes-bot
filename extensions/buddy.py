import dippy
import nextcord

from extensions.kudos.manager import KudosManager

class BuddyBumpExtenson(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager

    def __init__(self):
        super().__init__()

    @dippy.Extension.listener("message")
    async def on_message(self, message: nextcord.Message):
        if self._message_should_cost_kudos(message):
            await self._charge_for_message(message)

    async def _charge_for_message(self, message: nextcord.Message):
        user = message.mentions[0]
        kudos = await self.kudos.get_kudos(user)
        cost = int(message.content.split()[message.content.split().index("pay")+1])

        if kudos < cost:
            await message.channel.send(
                f"🔴 {user.mention}, you don't have enough kudos! You only have {kudos} kudos left.",
                delete_after=8,
            )
        else:
            await self.kudos.take_kudos(
                user, cost, f"Bumped a buddy post in {message.channel.mention}!"
            )
            await message.channel.send(
                f"🟢 {user.mention}, your bump was successful. You have {kudos - cost:,} kudos remaining.",
                delete_after=8,
            )

    def _message_should_cost_kudos(self, message: nextcord.Message) -> bool:
        if not message.author.bot:
            return False
        
        # Replace with id of #looking-for-buddy, the channel with all the buddy posts
        if message.channel.id != 987390245207150663:
            return False

        return "🟠" in message.content
