from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from .core import Dispander

if TYPE_CHECKING:
    import discord


class ExpandDiscordMessageFromUrlCog(commands.Cog):
    """A Discord.py cog that automatically calls dispander method."""

    def __init__(self, bot: commands.Bot) -> None:
        self.dispander = Dispander(bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:  # noqa: D102 # because this method is event listener
        if message.author.bot:
            return
        await self.dispander.dispand(message=message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:  # noqa: D102 # because this method is event listener
        await self.dispander.delete_dispand(payload=payload)
