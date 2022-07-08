import dippy
import nextcord
import re
from extensions.kudos.manager import KudosManager


class BuddyBumpExtenson(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager

    def __init__(self):
        super().__init__()

    @dippy.Extension.listener("raw_message_edit")
    async def on_raw_message_edit(self, payload):
        if self._message_should_cost_kudos(payload):
            await self._charge_for_message(payload)

    async def _charge_for_message(self, payload):
        message = await self.client.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )
        message_description = message.embeds[1].description
        user_id = int(re.search(r"\d+", message_description.split()[0])[0])
        user = self.client.get_guild(payload.guild_id).get_member(user_id)

        kudos = await self.kudos.get_kudos(user)
        cost = int(
            message_description.split()[message_description.split().index("kudos.") - 1]
        )

        response_embed = nextcord.Embed(
            title="🔴 Error: You don't have enough kudos!",
            description=f"{user.mention} You only have {kudos} kudos left.",
        )

        if kudos >= cost:
            await self.kudos.take_kudos(
                user, cost, f"Bumped a buddy post in {message.channel.mention}!"
            )

            response_embed.title = "🟢 Success: Post bumped!"
            response_embed.description = f"{user.mention}, you paid {cost} kudos to bump a post.\nYou have {kudos - cost:,} kudos remaining."

        await message.channel.send(embed=response_embed, delete_after=8)

    def _message_should_cost_kudos(self, payload) -> bool:
        if (
            "bot" not in payload.data["author"].keys()
            or not payload.data["author"]["bot"]
        ):
            return False
        
         # Replace with id of #looking-for-buddy, the channel with all the buddy posts
        if payload.channel_id != 987390245207150663:
            return False

        if len(payload.data["embeds"]) < 2:
            return False

        return "🟠 Bumping post..." in payload.data["embeds"][1]["title"]
