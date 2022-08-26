from discord.ext import commands

from .cog import ExpandDiscordMessageUrl
from .module import Dispander, delete_dispand, dispand

__all__ = ('dispand', 'delete_dispand', 'Dispander')


async def setup(bot: commands.Bot):
    await bot.add_cog(ExpandDiscordMessageUrl(bot))
