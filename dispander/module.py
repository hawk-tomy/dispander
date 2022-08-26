from __future__ import annotations

import re
from dataclasses import dataclass
from os import getenv
from typing import TYPE_CHECKING

from discord import Client, Colour, Embed, Guild, Message, RawReactionActionEvent, abc

__all__ = ('dispand', 'delete_dispand')

if TYPE_CHECKING:
    from typing import Union

    from discord import Emoji, PartialEmoji


regex_discord_message_url = (
    '(?!<)https://(ptb.|canary.)?discord(app)?.com/channels/'
    '(?P<guild>[0-9]{17,20})/(?P<channel>[0-9]{17,20})/(?P<message>[0-9]{17,20})(?!>)'
)
regex_extra_url = (
    r'\?base_aid=(?P<base_author_id>[0-9]{17,20})'
    '&aid=(?P<author_id>[0-9]{17,20})'
    '&extra=(?P<extra_messages>(|[0-9,]+))'
)


@dataclass()
class FromJumpUrl:
    base_author_id: int
    author_id: int
    extra_messages: list[int]


class Dispander:
    def __init__(
        self,
        bot: Client,
        delete_reaction_emoji: Union[None, str, Emoji, PartialEmoji]=None,
        embed_color: Union[None, int, Colour]=None
    ):
        self.bot = bot
        self.delete_reaction_emoji = delete_reaction_emoji
        self.embed_color = embed_color

    @property
    def bot(self)-> Client:
        return self.__bot

    @bot.setter
    def bot(self, bot: Client):
        if bot is not None and not isinstance(bot, Client): # type: ignore
            raise TypeError('bot must be discord.Client or subclass')
        self.__bot = bot

    @property
    def delete_reaction_emoji(self)-> Union[str, Emoji, PartialEmoji]:
        return self.__delete_reaction_emoji

    @delete_reaction_emoji.setter
    def delete_reaction_emoji(self, emoji: Union[str, Emoji, PartialEmoji, None]):
        if emoji is None:
            emoji = getenv("DELETE_REACTION_EMOJI", "\U0001f5d1")
        self.__delete_reaction_emoji = emoji

    @property
    def embed_color(self)-> Union[int, Colour]:
        return self.__embed_color

    @embed_color.setter
    def embed_color(self, color: Union[None, int, Colour]):
        if color is None:
            color = int(getenv('DEFAULT_EMBED_COLOR', 0))
        self.__embed_color = color

    async def dispand(self, message: Message)-> None:
        messages = await self.extract_message(message)
        for msg in messages:
            embeds: list[Embed]= []

            if msg.content or msg.attachments:
                embeds.append(self.compose_embed(msg))

            for attachment in msg.attachments[1:]:
                if not (attachment.content_type or '').startswith('image'):
                    continue # CUSTOMIZE: attachment.content_type

                embeds.append(
                    Embed(color=self.embed_color).set_image(url=attachment.proxy_url)
                    # CUSTOMIZE: attachment.proxy_url
                )

            embeds.extend(msg.embeds)

            if not embeds:
                continue

            sent_messages: list[Message]= []
            for i in range(0, len(embeds), 10):
                sent_messages.append(await message.channel.send(embeds=embeds[i:i+10]))

            main_message = sent_messages.pop(0)
            main_embeds = main_message.embeds.copy()
            await main_message.add_reaction(self.delete_reaction_emoji)
            if main_embeds[0].author.name:
                main_embeds[0].set_author(
                    name=main_embeds[0].author.name,
                    icon_url=main_embeds[0].author.icon_url,
                    url=self.make_jump_url(message, msg, sent_messages)
                )
            else:
                main_embeds.insert(0, Embed(color=self.embed_color).set_author(
                    name='jump to origin message',
                    url=self.make_jump_url(message, msg, sent_messages)
                ))
            await main_message.edit(embeds=main_embeds)

    async def delete_dispand(self, *, payload: RawReactionActionEvent)-> None:
        if str(payload.emoji) != self.delete_reaction_emoji:
            return

        assert self.bot.user is not None
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        assert isinstance(channel, abc.Messageable)

        message: Message= await channel.fetch_message(payload.message_id)
        if message.author.id != self.bot.user.id:
            return
        elif not message.embeds:
            return

        embed = message.embeds[0]
        if embed.author.url is None:
            return

        data = self.from_jump_url(embed.author.url)
        if payload.user_id not in (data.base_author_id, data.author_id):
            return

        await message.delete()
        for message_id in data.extra_messages:
            extra_message = await message.channel.fetch_message(message_id)
            if extra_message is not None:
                await extra_message.delete()

    async def extract_message(self, message: Message)-> list[Message]:
        messages: list[Message]= []
        assert message.guild is not None
        for ids in re.finditer(regex_discord_message_url, message.content):
            if message.guild.id != int(ids['guild']):
                continue
            messages.append(
                await self.fetch_message_from_id(message.guild, int(ids['channel']), int(ids['message']))
            )
        return messages

    async def fetch_message_from_id(self, guild: Guild, channel_id: int, message_id: int)-> Message:
        ch = await guild.fetch_channel(channel_id)
        assert isinstance(ch, abc.Messageable)
        return await ch.fetch_message(message_id)

    def make_jump_url(self, base_message: Message, dispand_message: Message, extra_messages: list[Message])-> str:
        """
        make jump url which include more information
        :param base_message: メッセージリンクが貼られていたメッセージ
        :param dispand_message: 展開中のメッセージ
        :param extra_messages: 展開する際にでた二つ目以降のメッセージ(e.g. 画像やembed)
        :return: 混入が完了したメッセージリンク
        """
        # base_aid: メッセージリンクで飛べる最初のメッセージの送信者のid
        # aid: メッセージリンクを送信したユーザーのid
        return (
            f'{dispand_message.jump_url}'
            f'?base_aid={dispand_message.author.id}'
            f'&aid={base_message.author.id}'
            f'&extra={",".join(str(msg.id) for msg in extra_messages)}'
        )

    def from_jump_url(self, url: str)-> FromJumpUrl:
        """
        メッセージリンクから情報を取得します。
        :param url: メッセージリンク
        :return: dict
        """
        base_url_match = re.match(regex_discord_message_url + regex_extra_url, url)
        assert base_url_match is not None
        data = base_url_match.groupdict()
        return FromJumpUrl(
            base_author_id=int(data["base_author_id"]),
            author_id=int(data["author_id"]),
            extra_messages=[int(_id) for _id in data["extra_messages"].split(",")] if data["extra_messages"] else []
        )

    def compose_embed(self, message: Message)-> Embed:
        if message.author.avatar:
            avatar_url = message.author.display_avatar.url
            # CUSTOMIZE: message.author.display_avatar.url (author.avater is used here)
        else:
            avatar_url = None
        assert message.guild
        if message.guild.icon:
            icon_url = message.guild.icon.url # CUSTOMIZE: message.guild.icon
        else:
            icon_url = None
        embed = Embed(
            description=message.content, # CUSTOMIZE: message.content
            timestamp=message.created_at,
            color=self.embed_color
        ).set_author(
            name=message.author.display_name, # CUSTOMIZE: message.author.display_name
            icon_url=avatar_url,
            url=message.jump_url # replace after send
        ).set_footer(
            text=message.channel.name, # type: ignore # CUSTOMIZE: message.channel.name
            icon_url=icon_url
        )
        if (
            message.attachments
            and (attachment:=message.attachments[0]).proxy_url
            and (attachment.content_type or '').startswith('image') # CUSTOMIZE: attachment.content_type
        ):
            embed.set_image(url=attachment.proxy_url) #CUSTOMIZE: attachment.proxy_url
        return embed


dispander_instance: Dispander= None # type: ignore


def init_global_instance(bot: Client):
    global dispander_instance
    if dispander_instance is None:
        dispander_instance = Dispander(bot)
    elif dispander_instance.bot is not None:
        return
    elif bot is not None:
        dispander_instance.bot = bot


async def delete_dispand(bot: Client, *, payload: RawReactionActionEvent)-> None:
    init_global_instance(bot)
    return await dispander_instance.delete_dispand(payload=payload)


async def dispand(message: Message)-> None:
    init_global_instance(None) # type: ignore
    return await dispander_instance.dispand(message)
