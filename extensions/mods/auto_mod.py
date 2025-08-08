import os

import nextcord

from aiohttp import ClientSession
from collections import deque
from datetime import datetime, timedelta, timezone
from nextcord import Embed, Guild, Member, Message, Role, TextChannel, utils
from nextcord.errors import NotFound
from nextcord.webhook import Webhook
from typing import Optional
from textwrap import wrap
import dippy
import re


class AutoModExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.Logging

    def __init__(self):
        super().__init__()
        self._message_buffer = deque(maxlen=1000)
        self._warned = {}
        self._muting = set()


    @dippy.Extension.listener("message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if message.channel.permissions_for(message.author).manage_messages:
            return

        self.client.loop.create_task(self._scan_for_links(message))

        if (
            message.author.id in self._muting
            or (message.author.communication_disabled_until and message.author.communication_disabled_until > datetime.utcnow())
        ):
            return

        self._message_buffer.appendleft(message)
        self.client.loop.create_task(self._scan_for_webhooks(message))
        self.client.loop.create_task(self._scan_for_discord_invites(message))
        await self._handle_spamming_violations(message, message.channel, message.author)

    @dippy.Extension.listener("message_edit")
    async def on_message_edit(self, _, message: Message):
        content = message.content.casefold()
        if "@everyone" in content or "@here" in content:
            await message.channel.send(
                f"{message.author.mention} please do not mention everyone **(your edited message has been deleted)**"
            )
            await message.delete()

    async def _scan_for_links(self, message: Message):
        blocked_links = [
            tld.lower()
            for tld in re.findall(
                r"([a-z0-9_./:\-]+\.(?:gay|xxx))", message.content, re.I
            )
        ]
        if not blocked_links:
            return

        links = " | ".join(blocked_links)
        tlds = ", ".join(link.rpartition(".")[-1] for link in blocked_links)
        content = (
            message.content
            if len(message.content) < 800
            else message.content[:800].strip() + "..."
        )
        try:
            await message.delete()
        except NotFound:
            pass
        await message.channel.send(
            content=message.author.mention,
            embed=Embed(
                title=f"Blocked Web TLDs",
                description=(
                    f"To maintain a wholesome and friendly environment we block all links to websites using certain "
                    f"TLDs. Your message has been deleted.\n\n**Detected TLD(s)**\n{tlds}"
                ),
                color=0xFF0000,
            ),
        )
        await self.client.get_channel(719311864479219813).send(
            embed=Embed(
                title=f"Blocked Web TLDs",
                description=(
                    f"**User:** {message.author.mention} ({message.author})\n**Links**: {links}\n**Channel**: "
                    f"{message.channel.mention}\n**Message**\n{content}"
                ),
                color=0xFF0000,
            ),
        )

    async def _scan_for_webhooks(self, message: Message):
        webhooks = re.findall(
            r"https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9-_]+", message.content
        )
        for webhook in webhooks:
            await self._delete_webhook(webhook)

        if webhooks:
            title = f"{len(webhooks)} Webhooks" if len(webhooks) > 1 else "A Webhook"
            hooks = "\n".join(f"`{hook}`" for hook in webhooks)
            await message.channel.send(
                embed=Embed(
                    title=f"🗑 Deleted {title}",
                    description=(
                        f"Anyone can send messages to a webhook. For this reason we call the delete method on all "
                        f"webhooks that we detect. You will need to create a new webhook to replace the ones we "
                        f"deleted. Be sure to not share your webhooks publicly."
                    ),
                    color=0xFF0000,
                ).add_field(name="Deleted Webhooks", value=hooks),
                reference=message,
            )

    async def _delete_webhook(self, webhook: str):
        async with ClientSession() as session:
            hook = Webhook.from_url(webhook, session=session)
            try:
                await hook.delete()
            except NotFound:
                pass  # Don't care, just want it gone

    async def _scan_for_discord_invites(self, message: Message):
        if message.author.bot:
            return

        # Allow discord invite links in the private chat channel category
        if message.channel.category.id == 833078627935322152:
            return

        # Allow staff to share invite links in any channel
        if (
            self.client.get_channel(720663441966366850)
            .permissions_for(message.author)
            .send_messages
        ):
            return

        # Allow anyone with the manage messages perms to share invite links
        if message.channel.permissions_for(message.author).manage_messages:
            return

        invites = re.findall(r"discord.gg/[a-z\d]+", message.content.casefold())
        if not invites:
            return

        try:
            await message.reply(
                embeds=[
                    nextcord.Embed(
                        description=(
                            f"❌ {message.author.mention} you are not allowed to share Discord invites in this channel."
                        ),
                        color=0xAA0000,
                    )
                ],
                mention_author=True,
            )
        finally:
            await message.delete()

        formatted_links = "\n- ".join(invites)
        await self.client.get_channel(719311864479219813).send(
            embeds=[
                nextcord.Embed(
                    description=(
                        f"{message.author} sent {len(invites)} Discord invite{'s' if len(invites) > 1 else ''} in "
                        f"{message.channel.mention}."
                    ),
                    color=0xCCAA00,
                ).add_field(name="Links", value=f"- {formatted_links}")
            ]
        )

    async def _handle_spamming_violations(
        self, message: Message, channel: TextChannel, member: Member, edit: bool = False
    ):
        last_warned = (
            self._warned[member.id] + timedelta(seconds=2)
            if member.id in self._warned
            else None
        )
        should_mute = last_warned and datetime.utcnow() - last_warned <= timedelta(
            minutes=2
        )
        (
            num_messages_last_five_seconds,
            num_channels_last_fifteen_seconds,
            num_duplicate_messages,
            num_everyone_mentions,
            num_everyone_mentions_with_nitro,
            num_scam_links,
        ) = self._metrics_on_messages_from_member(member, last_warned)

        if member.id == 335491211039080458:
            content = self.escape_links(message.clean_content)
            wrapped = "\n> ".join(wrap(content, 80))
            print(
                f"Member Spam Stats\n"
                f"- Messages last 5 seconds:  {num_messages_last_five_seconds}\n"
                f"- Channels last 15 seconds: {num_channels_last_fifteen_seconds}\n"
                f"- Duplicate messages:       {num_duplicate_messages}\n"
                f"- Everyone mentions:        {num_everyone_mentions}\n"
                f"- Nitro scams:              {num_everyone_mentions_with_nitro}\n\n"
                f"- Scam links:               {num_scam_links}\n\n"
                f"Message Content\n"
                f"> {wrapped}"
            )

        too_many_messages = num_messages_last_five_seconds > 5
        too_many_channels = num_channels_last_fifteen_seconds > 3
        too_many_duplicates = num_duplicate_messages > 1
        too_many_everyone_mentions = num_everyone_mentions > 0
        too_many_everyone_mentions_with_nitro = num_everyone_mentions_with_nitro > 0
        too_many_scam_links = num_scam_links > 0

        if (
            not too_many_messages
            and not too_many_channels
            and not too_many_duplicates
            and not too_many_everyone_mentions
            and not too_many_everyone_mentions_with_nitro
            and not too_many_scam_links
        ):
            return

        should_mute = (
            should_mute or too_many_everyone_mentions_with_nitro or too_many_scam_links
        )

        action_description = []
        if should_mute:
            action_description.append(
                f"{member.mention} you're being muted until the mods can review your behavior:\n"
            )
            if too_many_messages:
                action_description.append("- Message spamming\n")
            if too_many_channels:
                action_description.append("- Spamming in multiple channels\n")
            if too_many_duplicates:
                action_description.append("- Sending duplicate messages\n")
            if too_many_everyone_mentions or too_many_everyone_mentions_with_nitro:
                action_description.append("- Spamming mentions to everyone\n")
            if too_many_everyone_mentions_with_nitro or too_many_scam_links:
                action_description.append("- Nitro scamming\n")

        else:
            if too_many_messages:
                action_description.append(" spamming messages")
            if too_many_channels:
                action_description.append(" messaging in so many channels")
            if too_many_duplicates:
                action_description.append(" sending duplicate messages")
            if too_many_everyone_mentions or too_many_everyone_mentions_with_nitro:
                action_description.append(" mentioning everyone")
            if too_many_everyone_mentions_with_nitro or too_many_scam_links:
                action_description.append(" nitro scamming")

            if len(action_description) > 1:
                action_description[-1] = f" and{action_description[-1]}"
            if len(action_description) > 2:
                action_description = [",".join(action_description)]

            action_description.insert(0, f"{member.mention} please stop")

        if should_mute:
            self._muting.add(member.id)
            timeout_duration = timedelta(hours=24)
            await member.edit(timeout=timeout_duration, reason="Auto-moderation violation")
            self._muting.remove(member.id)

        if (
            num_everyone_mentions > 0
            or num_scam_links > 0
            or num_everyone_mentions_with_nitro > 0
        ):
            self.client.loop.create_task(
                self.log_scam_links(self.get_all_sanitized_links(message.content))
            )
            await message.delete()
            action_description.append("\n**⚠️ Your message has been deleted ⚠️**")

        if too_many_everyone_mentions_with_nitro or too_many_scam_links:
            m: Message = (await channel.history(limit=1).flatten())[0]
            await channel.send(
                f"{member.mention} you've been timed out for possibly sharing scams.",
                delete_after=5,
            )
        else:
            m: Message = await channel.send("".join(action_description))

        if should_mute:
            mods: Role = channel.guild.get_role(644390354157568014)
            mod_channel = self.client.get_channel(728249959098482829)
            await mod_channel.send(
                f"{mods.mention} please review {member.mention}'s behavior in {channel.mention} {m.jump_url}.\n"
                f"Use Discord's timeout management to remove the timeout.\nOriginal message:"
            )
            # Forward the actual message
            try:
                await message.forward(mod_channel)
            except Exception as e:
                # Fallback to text if forwarding fails
                content = self.escape_links(message.clean_content)
                wrapped = "\n> ".join(wrap(content, 80))
                await mod_channel.send(f"```\n{wrapped[:900]}\n```")
        self._warned[member.id] = datetime.utcnow()

    async def log_scam_links(self, links: set[str]):
        async with ClientSession() as session:
            webhook = Webhook.from_url(os.getenv("SCAM_LINKS_WEBHOOK"), session=session)
            for link in links:
                await webhook.send(link)

    def _metrics_on_messages_from_member(
        self, member: Member, oldest: Optional[datetime] = None
    ) -> tuple[int, ...]:
        num_messages_checked = 0
        num_recent_messages = 0
        num_everyone_mentions = 0
        num_everyone_mentions_with_nitro = 0
        num_scam_links = 0
        recent_channels = set()
        messages_last_minute = set()

        now = datetime.now()
        oldest = oldest if oldest else now
        since = min(oldest, now - timedelta(minutes=1)).astimezone(timezone.utc)
        now = now.astimezone(timezone.utc)
        for message in (
            message for message in self._message_buffer if message.author == member
        ):
            if since > message.created_at:
                break

            if now - timedelta(seconds=5) <= message.created_at:
                num_recent_messages += 1

            if now - timedelta(seconds=15) <= message.created_at:
                recent_channels.add(message.channel.id)

                content = message.content.casefold()
                links = self.get_scam_links(content)
                if links:
                    num_scam_links += len(links)

                if "@everyone" in content or "@here" in content:
                    num_everyone_mentions += 1

                    if "nitro" in content or "gift" in content:
                        num_everyone_mentions_with_nitro += 1

            if len(message.content) > 15:
                messages_last_minute.add(message.content)
                num_messages_checked += 1

        return (
            num_recent_messages,
            len(recent_channels),
            num_messages_checked - len(messages_last_minute),
            num_everyone_mentions,
            num_everyone_mentions_with_nitro,
            num_scam_links,
        )

    def get_all_sanitized_links(self, content: str) -> set[str]:
        return {
            " ".join(parts)
            for parts in re.findall(
                r"(http[s]?://)(.+?\..+?)(/[^\s]*|$)", content.casefold()
            )
        }

    def get_scam_links(self, content: str) -> set[str]:
        return {
            link
            for link in re.findall(
                r"http[s]?://(?:d.+?\.gift|t\.me)/[^\s]+", content.casefold()
            )
            if not link.startswith("https://discord.gift/")
        }

    def escape_links(self, content: str) -> str:
        escaped = re.sub(r"(http[s]?://)(.+?)(\s|\/|$)", r"\1 \2 \3", content)
        escaped = re.sub(r"discord\.gg", r"discord . gg", escaped)
        return escaped
