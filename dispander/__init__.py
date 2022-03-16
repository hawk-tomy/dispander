from discord.ext import commands


from .module import dispand, delete_dispand
from .cog import ExpandDiscordMessageUrl


__all__ = ('dispand', 'delete_dispand')


async def setup(bot: commands.Bot):
    await bot.add_cog(ExpandDiscordMessageUrl(bot))
