from extensions.kudos.manager import KudosManager
from extensions.mods.mod_manager import ModManager
from nextcord import Guild, Member, Message, MessageType, TextChannel, utils
from datetime import datetime, timedelta, timezone
from typing import Optional
import re
import asyncio
import dippy.labels
import dippy


class NewMemberExtension(dippy.Extension):
    client: dippy.Client
    kudos: KudosManager
    labels: dippy.labels.storage.StorageInterface
    mod_manager: ModManager
    log: dippy.Logging

    @dippy.Extension.listener("ready")
    async def onboard_new_members(self):
        guild = self.client.get_guild(644299523686006834)
        role = guild.get_role(888160821673349140)
        for member in role.members:
            if (
                    re.match(r"^[A-Za-z0-9]+_\d[A-Za-z0-9_.]+$", member.name)
                    and
                    datetime.utcnow().replace(tzinfo=timezone.utc) - member.created_at < timedelta(days=180)
                    and
                    member.avatar is None
            ):
                await member.ban(delete_message_seconds=60 * 60, reason="Bot accounts")
                await member.guild.get_channel(719311864479219813).send(
                    f"Auto banned {member.name} (aka {member.display_name})"
                )
                continue

            joined_time = await member.get_label("joined")
            if joined_time is None:
                await asyncio.gather(
                    self.onboard_member(member),
                    self.check_for_highscore(member.guild),
                )
            else:
                joined = datetime.fromisoformat(joined_time)
                await self.schedule_onboarding(member, joined)

    @dippy.Extension.listener("ready")
    async def assign_missing_roles(self):
        guild = self.client.get_guild(644299523686006834)
        need_roles = []
        for member in guild.members:
            if len(member.roles) < 2 and not member.pending:
                need_roles.append(self.onboard_member(member))

        if need_roles:
            await asyncio.gather(*need_roles)
            await guild.get_channel(865010559861522442).send(
                f"Restarted and added roles to {len(need_roles)} members"
            )

    @dippy.Extension.command("!set welcome channel")
    async def set_welcome_channel(self, message: Message):
        if not message.author.guild_permissions.manage_channels:
            return

        await self.labels.set(
            "guild",
            message.guild.id,
            "welcome_channel_id",
            message.channel_mentions[0].id,
        )

    @dippy.Extension.command("!reset member counter")
    async def reset_member_counter(self, message: Message):
        if not message.author.guild_permissions.administrator:
            return

        await message.guild.set_label("highest-member-count", 0)
        await self.check_for_highscore(message.guild)

    @dippy.Extension.listener("member_update")
    async def member_accepts_rules(self, before: Member, after: Member):
        if (
            re.match(r"^[A-Za-z0-9]+_\d[A-Za-z0-9_.]+$", after.name)
            and
            datetime.utcnow().replace(tzinfo=timezone.utc) - after.created_at < timedelta(days=180)
            and
            after.avatar is None
        ):
            await after.ban(delete_message_seconds=60*60, reason="Bot accounts")
            await after.guild.get_channel(719311864479219813).send(f"Auto banned {after.name} (aka {after.nick})")
            return

        if before.pending and not after.pending:
            self.log.info(f"Got member {before.display_name}")
            await asyncio.gather(
                self.add_unwelcomed_user(after),
                self.onboard_member(after),
                self.check_for_highscore(after.guild),
            )

    async def check_for_highscore(self, guild: Guild):
        if await self.mod_manager.locked_down(guild):
            return

        announce_channel_id = 644299524151443487
        last_highest = await guild.get_label("highest-member-count", default=0)
        count = self.get_num_members(guild)
        if count > last_highest or last_highest - count > 20:
            await guild.set_label("highest-member-count", count)
            rounded = count // 250 * 250
            if rounded > last_highest and rounded % 10_000 == 0:
                action = "reached" if count == rounded else "passed"
                await guild.get_channel(announce_channel_id).send(
                    ("🎉🥳🎈" * 5 + "🥳" + "🎈🥳🎉" * 5 + "\n") * 2
                    + f"🎉🥳🎈 **We've {action} {rounded:,} members!!!** 🎈🥳🎉\n"
                    + ("\n" + "🎉🥳🎈" * 5 + "🥳" + "🎈🥳🎉" * 5) * 2
                )
                await guild.get_channel(announce_channel_id).send(
                    "https://media.giphy.com/media/26tOZ42Mg6pbTUPHW/giphy.gif"
                )
            elif rounded > last_highest:
                action = "reached" if count == rounded else "passed"
                await guild.get_channel(announce_channel_id).send(
                    f"🎉🥳🎈 **We've {action} {rounded:,} members!!!** 🎈🥳🎉"
                )

    async def onboard_member(self, member: Member):
        joined = datetime.now().astimezone(timezone.utc)
        await member.set_label("joined", joined.isoformat())
        await self.schedule_onboarding(member, joined)
        await asyncio.sleep(3)
        await member.add_roles(member.guild.get_role(888160821673349140))

    async def schedule_onboarding(self, member: Member, joined: datetime):
        async def onboard():
            try:
                await member.add_roles(member.guild.get_role(644325811301777426))
            except:
                pass
            else:
                await member.remove_roles(member.guild.get_role(888160821673349140))

        now = datetime.now().astimezone(timezone.utc)
        when = joined + timedelta(days=2)
        if when <= now:
            await onboard()
        else:
            asyncio.get_running_loop().call_later(
                (when - now).total_seconds(),
                lambda: asyncio.get_running_loop().create_task(onboard()),
            )

    def get_num_members(self, guild: Guild) -> int:
        return sum(1 for member in guild.members if not member.bot)

    @dippy.Extension.listener("message")
    async def welcome_messages(self, message: Message):
        if message.author.bot or not isinstance(message.channel, TextChannel):
            return

        if message.type not in {MessageType.default, MessageType.reply}:
            return

        channel = await self.get_welcome_channel(message.guild)
        if message.channel != channel:
            return

        unwelcomed_members = await self.get_unwelcomed_users(message.guild)
        if not unwelcomed_members or message.author in unwelcomed_members:
            return

        welcoming = ", ".join(f"{member}<{member.id}>" for member in unwelcomed_members)
        self.log.info(f"{message.author} is welcoming {welcoming}")
        await self._give_kudos_for_welcoming(
            message.author, len(unwelcomed_members), channel
        )

    async def get_welcome_channel(self, guild: Guild) -> Optional[TextChannel]:
        channel_id = await self.labels.get("guild", guild.id, "welcome_channel_id")
        return channel_id and guild.get_channel(channel_id)

    async def get_unwelcomed_users(self, guild: Guild) -> list[Member]:
        return [
            guild.get_member(member_id)
            for member_id in await self.labels.get(
                "guild", guild.id, "unwelcomed_members", []
            )
        ]

    async def add_unwelcomed_user(self, member: Member):
        if member.id == 335491211039080458:
            return  # Ignore dev alt

        unwelcomed = await self.get_unwelcomed_users(member.guild)
        unwelcomed.append(member)
        await self._set_unwelcomed_users(member.guild, unwelcomed)
        self.log.info(f"Added {member.display_name} to list of unwelcomed members")

    async def clear_unwelcomed_users(self, guild: Guild):
        await self._set_unwelcomed_users(guild, [])

    async def _give_kudos_for_welcoming(
        self, member: Member, num_welcomed: int, channel: TextChannel
    ):
        kudos = 2 * num_welcomed
        await self.clear_unwelcomed_users(member.guild)
        await self.kudos.give_kudos(
            member,
            kudos,
            f"{member.mention} welcomed {num_welcomed} member{'s' * (num_welcomed > 1)} to the server!!!",
        )
        expert_emoji = utils.get(member.guild.emojis, name="expert")
        await channel.send(
            f"{expert_emoji} {member.mention} you got {kudos} kudos for welcoming {num_welcomed} "
            f"member{'s' * (num_welcomed > 1)}!",
            delete_after=5,
        )

    async def _set_unwelcomed_users(self, guild: Guild, unwelcomed: list[Member]):
        await self.labels.set(
            "guild",
            guild.id,
            "unwelcomed_members",
            [member.id for member in unwelcomed if member],
        )
