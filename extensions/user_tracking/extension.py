from extensions.user_tracking.manager import UserTracker
import dippy
import nextcord


class UserTrackingExtension(dippy.Extension):
    client: dippy.Client
    manager: UserTracker

    @dippy.Extension.listener("member_update")
    async def nickname_changed(self, before: nextcord.Member, after: nextcord.Member):
        if before.nick == after.nick:
            return

        await self.manager.add_username_to_history(after, before.display_name)

    @dippy.Extension.listener("user_update")
    async def username_changed(self, before: nextcord.User, after: nextcord.User):
        if before.name == after.name:
            return

        for guild in after.mutual_guilds:
            member: nextcord.Member = guild.get_member(after.id)
            if not member.nick:
                await self.manager.add_username_to_history(member, before.name)
