from unicodedata import category
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

        category = await self.get_buddy_chat_category(message.guild)
        if not category:
            return

        channel_name = await self._get_channel_name(message.mentions)
        overwrites = category.overwrites.copy()
        for member in message.mentions:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
        mentions = ", ".join(member.mention for member in message.mentions)
        await channel.send(
            f"***TEST MESSAGE***"
        )


    async def _get_channel_name(self, members: list[discord.Member]) -> str:
        slugs = (self.channel_manager.sluggify(member.name, sep="") for member in members)
        return '-'.join(self.channel_manager._get_prefix(slug) for slug in slugs)