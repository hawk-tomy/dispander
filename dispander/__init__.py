from discord.ext import commands

from .cogs import ExpandDiscordMessageFromUrlCog


async def setup(bot: commands.Bot):
    await bot.add_cog(ExpandDiscordMessageFromUrlCog(bot))
