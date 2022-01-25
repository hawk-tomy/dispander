from __future__ import annotations

import discord
from discord.ext import commands

from .module import delete_dispand, dispand

__all__ = ('ExpandDiscordMessageUrl',)


class ExpandDiscordMessageUrl(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await dispand(message=message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await delete_dispand(bot=self.bot, payload=payload)
