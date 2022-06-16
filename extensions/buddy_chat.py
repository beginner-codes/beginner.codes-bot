import dippy
import dippy.labels
import discord
from extensions.help_channels.channel_manager import ChannelManager


class BuddyChatExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.logging.Logging
    labels: dippy.labels.storage.StorageInterface
    channel_manager: ChannelManager

    @dippy.Extension.command("!set buddychat category")
    async def set_buddy_chat_category_command(self, message: discord.Message):
        if not message.author.guild_permissions.administrator:
            return

        category_name = message.content.removeprefix("!set buddychat category ").strip()
        guild: discord.Guild = message.guild
        category = discord.utils.get(guild.categories, name=category_name)

        
        if not category:
            await message.channel.send(
                f"Couldn't find a category named {category_name!r}"
            )
            return

        await self.set_buddy_chat_category(guild, category)
        await message.channel.send(
            f"Set {category_name} as the buddy chat category for {guild.name}"
        )


    async def set_buddy_chat_category(
        self, guild: discord.Guild, category: discord.CategoryChannel
    ) -> discord.CategoryChannel:
        await self.labels.set("guild", guild.id, "buddy-chat-category", category.id)


    async def get_buddy_chat_category(
        self, guild: discord.Guild
    ) -> discord.CategoryChannel:
        return guild.get_channel(
            await self.labels.get("guild", guild.id, "buddy-chat-category")
        )
    

    @dippy.Extension.command("!buddy")
    async def buddy_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        emoji = message.content.removeprefix("!buddy ").split()[0]
        if len(emoji) > 2:
            emoji = ""

        category = await self.get_buddy_chat_category(message.guild)

        channel_name = emoji + await self._get_channel_name(message.mentions)
        overwrites = category.overwrites.copy()
        for member in message.mentions:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
        member_names = ", ".join(member.display_name for member in message.mentions)
        welcome_msg = await channel.send(
            embed=discord.Embed(
                title=f"Welcome {member_names} to your buddy chat!",
                description=(
                    "**Recommended Structure**\n"
                    "**Daily**\n"
                    "Check in, talk about what you've been working on and any struggles.\n"
                    "**Weekly**\n"
                    "Set goals for the week, review them. Have you achieved your goals? If not, why not?\n"
                    "\n"
                    "**Goal Ideas**\n"
                    "- Start a new project.\n"
                    "- Start learning a new language.\n"
                    "- Implemenent a new feature in your project.\n"
                    "- Spent at least two hours a day programming.\n"
                ),
                color=0x00FF66
            )
        )
        await welcome_msg.pin()


    async def _get_channel_name(self, members: list[discord.Member]) -> str:
        slugs = (self.channel_manager.sluggify(member.name, sep="") for member in members)
        return '-'.join(self.channel_manager._get_prefix(slug) for slug in slugs)


    @dippy.Extension.command("!close")
    async def close_buddy_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_buddy_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        await message.channel.delete()


    @dippy.Extension.command("!archive")
    async def archive_buddy_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_buddy_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        message.channel: discord.TextChannel = message.channel
        await message.channel.edit(
            name=f"{message.channel.name}-archive", sync_permissions=True
        )
        await message.channel.send("🗂 This channel has been archived")


    @dippy.Extension.command("!add")
    async def add_buddy_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_buddy_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        overwrites = message.channel.overwrites.copy()
        for member in message.mentions:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        await message.channel.edit(overwrites=overwrites)


    @dippy.Extension.command("!remove")
    async def remove_buddy_chat_command(self, message: discord.Message):
        if not message.author.guild_permissions.kick_members:
            return

        category = await self.get_buddy_chat_category(message.guild)
        if not category or message.channel.category != category:
            return

        overwrites = message.channel.overwrites.copy()
        for member in message.mentions:
            overwrites[member] = discord.PermissionOverwrite(read_messages=False)
        await message.channel.edit(overwrites=overwrites)
