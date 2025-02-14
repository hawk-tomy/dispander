from __future__ import annotations

from typing import TYPE_CHECKING

from .cogs import ExpandDiscordMessageFromUrlCog

if TYPE_CHECKING:
    from discord.ext import commands


async def setup(bot: commands.Bot) -> None:
    """Setup function for discord.ext.commands.Bot.load_extension."""
    await bot.add_cog(ExpandDiscordMessageFromUrlCog(bot))
