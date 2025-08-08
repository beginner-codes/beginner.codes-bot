from typing import cast, Optional
import dippy.labels
import nextcord


class PremiumMemberExtension(dippy.Extension):
    client: dippy.Client
    labels: dippy.labels.storage.StorageInterface

    async def get_booster_channel(
        self, guild: nextcord.Guild
    ) -> Optional[nextcord.TextChannel]:
        channel_id = cast(
            int, await self.labels.get("guild", guild.id, "booster_channel_id")
        )
        return channel_id and guild.get_channel(channel_id)

    @dippy.Extension.listener("member_update")
    async def monitor_for_premium_members(
        self, before: nextcord.Member, member: nextcord.Member
    ):
        new_roles = set(member.roles) - set(before.roles)
        if not new_roles:
            return

        if not any(role.name == "Premium Members" for role in new_roles):
            return

        await self.send_premium_member_message(member)

    @dippy.Extension.command("!test premium member message")
    async def test_booster_channel_command(self, message: nextcord.Message):
        await self.send_premium_member_message(message.author, test=True)

    def count_premium_members(self, guild: nextcord.Guild) -> int:
        role = nextcord.utils.get(guild.roles, name="Premium Members")
        return len(role.members)

    async def send_premium_member_message(
        self, member: nextcord.Member, *, test: bool = False
    ):
        channel = await self.get_booster_channel(member.guild)
        await channel.send(
            embed=nextcord.Embed(
                description=(
                    f"<:foxaw:860665815350640650> {member.mention} has become a Premium Member!!! That's"
                    f" {self.count_premium_members(member.guild)} Premium Members!!! <:foxaw:860665815350640650>"
                ),
                color=0xFF008D,
            )
            .set_author(
                name=f"{member} Has Become a Premium Member!!!{' (TEST)' * test}",
                icon_url=member.avatar.url,
            )
            .set_thumbnail(
                url="https://media.discordapp.net/stickers/860666036340654132.webp"
            )
        )
