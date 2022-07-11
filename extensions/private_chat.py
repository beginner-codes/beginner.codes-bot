from datetime import datetime
import dippy.labels
import discord
import nextcord.types.threads


class PrivateChatExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface

    @dippy.Extension.command("!archive")
    async def archive_mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        channel = await self.get_mod_chat_channel(message.guild)
        if not channel or message.thread.parent != channel:
            return

        await message.thread.edit(
            archived=True, locked=True, name=f"{message.thread.name}-ARCHIVED"
        )
        await message.channel.send("🗂 This channel has been archived")

    @dippy.Extension.command("!lock")
    async def lock_mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        mod_role = await self.get_mod_role(message.guild)
        channel = await self.get_mod_chat_channel(message.guild)
        if not channel or message.thread.parent != channel:
            return

        for thread_member in message.thread.members:
            member = channel.guild.get_member(thread_member.id)
            if mod_role not in member.roles:
                await message.thread.remove_user(member)

        await message.thread.edit(
            archived=True, locked=True, name=f"{message.thread.name}-LOCKED"
        )
        await message.thread.send(
            "🔒 This thread has been closed, only mods have access"
        )

    @dippy.Extension.command("!modchat")
    async def mod_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        channel = await self.get_mod_chat_channel(message.guild)
        if not channel:
            return

        mod_role = await self.get_mod_role(message.guild)
        date = datetime.utcnow().strftime("%d-%m-%Y")
        thread = await channel.create_thread(
            name=f"Mod Chat: {date}", auto_archive_duration=3 * 24 * 60
        )

        await thread.send(
            # mod_role.mention,
            embeds=[
                nextcord.Embed(
                    description=f"You can discuss privately with the {mod_role.mention} here.",
                    color=0x33CC77,
                )
            ],
        )

        await thread.add_user(message.author)
        for mention in message.mentions:
            await thread.add_user(mention)

        mod_channel_id = await message.guild.get_label("mod_channel_id")
        await message.guild.get_channel(mod_channel_id).send(
            f"ℹ️ New mod chat channel created: {thread.mention}"
        )

    @dippy.Extension.command("!set modchat channel")
    async def set_mod_chat_channel_command(self, message: discord.Message):
        if not message.author.guild_permissions.administrator:
            return

        guild: discord.Guild = message.guild
        channel = message.channel_mentions and message.channel_mentions[0]
        if not channel:
            await message.channel.send(f"You must mention a channel")
            return

        await self.set_mod_chat_channel(guild, channel)
        await message.channel.send(
            f"Set {channel.mention} as the modchat channel for {guild.name}"
        )

    @dippy.Extension.command("!set mod role")
    async def set_mod_role_command(self, message: discord.Message):
        if not message.author.guild_permissions.administrator:
            return

        guild: discord.Guild = message.guild
        role = message.role_mentions and message.role_mentions[0]
        if not role:
            await message.channel.send(f"You must mention a role")
            return

        await self.set_mod_role(guild, role)
        await message.channel.send(f"Set {role} as the mod role {guild.name}")

    async def get_mod_chat_channel(self, guild: discord.Guild) -> discord.TextChannel:
        return guild.get_channel(
            await self.labels.get("guild", guild.id, "mod-chat-channel")
        )

    async def get_mod_role(self, guild: discord.Guild) -> discord.Role:
        return guild.get_role(await self.labels.get("guild", guild.id, "mod-role"))

    async def set_mod_chat_channel(
        self, guild: discord.Guild, channel: discord.TextChannel
    ):
        await self.labels.set("guild", guild.id, "mod-chat-channel", channel.id)

    async def set_mod_role(self, guild: discord.Guild, role: discord.Role):
        await self.labels.set("guild", guild.id, "mod-role", role.id)
