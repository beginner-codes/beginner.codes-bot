import re
import nextcord


def message_should_cost_kudos(message: nextcord.Message) -> bool:
    if message.author.bot:
        return False

    if message.channel.id != 659767976601583627:
        return False

    return bool(
        re.search(r"(?:https?://)?[^/.\s]+\.[^/\s]+(?:/\S*)?", message.content, re.I)
    )
