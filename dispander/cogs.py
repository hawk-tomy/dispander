from __future__ import annotations

import discord
from discord.ext import commands

from .core import Dispander


class ExpandDiscordMessageFromUrlCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.dispander = Dispander(bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await self.dispander.dispand(message=message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.dispander.delete_dispand(payload=payload)
