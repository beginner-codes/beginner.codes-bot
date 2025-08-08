from bevy import Injectable
from collections import UserDict
from dataclasses import dataclass, field
from dippy import Client
from nextcord import Member, utils, errors
from typing import Callable, Coroutine


@dataclass
class Achievement:
    name: str
    description: str
    unlock_description: str
    emoji: str
    kudos: int = -1
    days_active: int = -1
    awarded_handlers: set[Callable[[Member], Coroutine]] = field(default_factory=set)

    def on_awarded(self, callback: Callable[[Member], Coroutine]):
        self.awarded_handlers.add(callback)

    def __hash__(self):
        return hash(self.name)


class Achievements(UserDict, Injectable):
    client: Client

    def __init__(self):
        super().__init__(
            {
                "MUSIC_DJ": Achievement(
                    "Music DJ [LEGACY]",
                    (
                        "**[LEGACY]** ~~Music DJs get the 🎸Music DJ🎸 role while in voice chat allowing them full "
                        "control of the Rythm music bot.~~\n\n*The Rythm bot has shutdown, until we find a new use for "
                        "this achievement it offers no perks.*"
                    ),
                    (
                        "**[LEGACY]** You're a Music DJ! ~~When in voice chat you'll have the DJ role giving you full "
                        "control of the Rythm music bot!~~\n\n*The Rythm bot has shutdown, until we find a new use for "
                        "this achievement it offers no perks.*"
                    ),
                    "🎸",
                    250,
                ),
                "CODER": Achievement(
                    "Veteran Member",
                    (
                        "Veteran Members are the members who are most active in our community, asking questions, "
                        "helping others, participating in the fun, doing challenges, etc."
                    ),
                    "You're a Veteran Member! Thanks for being 😎 AWESOME 😎!!!",
                    "😎",
                    188,  # 4 weeks of daily activity
                ),
                "BUDDY": Achievement(
                    "Buddy",
                    "People with the buddy achievement get access to our Buddy system.",
                    "You've unlocked the Buddy achievement! You can now access and use our Buddy system.",
                    "🤝",
                    200,
                    28,
                ),
            }
        )

        self.on_award("CODER", self.give_veteran_members_role)
        self.on_award("BUDDY", self.give_buddy_role)

    async def awarded_achievement(self, member: Member, achievement: Achievement):
        if achievement.awarded_handlers:
            for handler in achievement.awarded_handlers:
                self.client.loop.create_task(handler(member))

    def on_award(self, achievement_key: str, callback: Callable[[Member], Coroutine]):
        self[achievement_key].on_awarded(callback)

    async def give_veteran_members_role(self, member: Member):
        role = utils.get(member.guild.roles, name="veteran members")
        try:
            await member.add_roles(role)
            await member.remove_roles(utils.get(member.guild.roles, name="member"))
            await self.client.get_channel(851228622832533534).send(
                f"{member.mention} you're awesome! Thank you for contributing and being such an amazing part of this "
                f"community! Now that you've unlocked the 😎Veteran Member😎 achievement you have access to this"
                f"channel!"
            )
        except errors.Forbidden:
            pass

    async def give_buddy_role(self, member: Member):
        role = utils.get(member.guild.roles, name="buddy")
        try:
            await member.add_roles(role)
            await self.client.get_channel(987141595453349928).send(
                f"{member.mention} thank you for proving you are a dedicated member of our community! You're now able "
                f"to use our Buddy System!"
            )
        except errors.Forbidden:
            pass
