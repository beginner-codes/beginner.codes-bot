from datetime import datetime, timedelta
from nextcord import Member, PermissionOverwrite, VoiceChannel, VoiceState, utils
from extensions.kudos.manager import KudosManager
import asyncio
import dippy
import dippy.labels


class VoiceChatExtension(dippy.Extension):
    @dippy.Extension.listener("voice_state_update")
    async def manage_vc_role(self, member: Member, _, after: VoiceState):
        role = member.guild.get_role(1154477563649998859)  # Voice Chat
        has_role = role in member.roles
        if has_role and after.channel is None:
            await member.remove_roles(role)
        elif not has_role and after.channel:
            await member.add_roles(role)
