from __future__ import annotations

import re
from os import getenv

from discord import Client, Embed, Guild, Message, RawReactionActionEvent

__all__ = ('dispand', 'delete_dispand')


regex_discord_message_url = (
    r'(?!<)https://(ptb.|canary.)?discord(app)?.com/channels/'
    r'(?P<guild>[0-9]{17,19})/(?P<channel>[0-9]{17,19})/(?P<message>[0-9]{17,19})(?!>)'
)
regex_extra_url = (
    r'\?base_aid=(?P<base_author_id>[0-9]{17,19})'
    r'&aid=(?P<author_id>[0-9]{17,19})'
    r'&extra=(?P<extra_messages>(|[0-9,]+))'
)
DELETE_REACTION_EMOJI = getenv("DELETE_REACTION_EMOJI", "\U0001f5d1")
EMBED_COLOR = int(getenv('DEFAULT_EMBED_COLOR', 0))


async def delete_dispand(bot: Client, *, payload: RawReactionActionEvent):
    if str(payload.emoji) != DELETE_REACTION_EMOJI:
        return
    if payload.user_id == bot.user.id:
        return

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    await _delete_dispand(bot, message, payload.user_id)


async def _delete_dispand(bot: Client, message: Message, operator_id: int):
    if message.author.id != bot.user.id:
        return
    elif not message.embeds:
        return

    embed = message.embeds[0]
    if getattr(embed.author, "url", None) is None:
        return
    data = from_jump_url(embed.author.url)
    if not (data["base_author_id"] == operator_id or data["author_id"] == operator_id):
        return
    await message.delete()
    for message_id in data["extra_messages"]:
        extra_message = await message.channel.fetch_message(message_id)
        if extra_message is not None:
            await extra_message.delete()


async def dispand(message: Message):
    messages = await extract_message(message)
    for m in messages:
        embeds: list[Embed]= []

        if m.content or m.attachments:
            embeds.append(compose_embed(m))

        for attachment in m.attachments[1:]:
            if not (attachment.content_type or '').startswith('image'):
                continue

            embeds.append(
                Embed(color=EMBED_COLOR).set_image(url=attachment.proxy_url)
            )

        embeds.extend(m.embeds)

        if not embeds:
            continue

        sent_messages: list[Message]= []
        for i in range(0, len(embeds), 10):
            sent_messages.append(await message.channel.send(embeds=embeds[i:i+10]))

        main_message = sent_messages.pop(0)
        main_embeds = main_message.embeds.copy()
        await main_message.add_reaction(DELETE_REACTION_EMOJI)
        if main_embeds[0].author.name:
            main_embeds[0].set_author(
                name=main_embeds[0].author.name,
                icon_url=main_embeds[0].author.icon_url,
                url=make_jump_url(message, m, sent_messages)
            )
        else:
            main_embeds.insert(0, Embed().set_author(
                name='jump to origin message',
                url=make_jump_url(message, m, sent_messages)
            ))
        await main_message.edit(embeds=main_embeds)


async def extract_message(message: Message)-> list[Message]:
    messages = []
    for ids in re.finditer(regex_discord_message_url, message.content):
        if message.guild.id != int(ids['guild']):
            continue
        messages.append(await fetch_message_from_id(message.guild, int(ids['channel']), int(ids['message'])))
    return messages


async def fetch_message_from_id(guild: Guild, channel_id: int, message_id: int)-> Message:
    ch = await guild.fetch_channel(channel_id)
    return await ch.fetch_message(message_id)


def make_jump_url(base_message: Message, dispand_message: Message, extra_messages: list[Message])-> str:
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


def from_jump_url(url: str)-> dict[str, str]:
    """
    メッセージリンクから情報を取得します。
    :param url: メッセージリンク
    :return: dict
    """
    base_url_match = re.match(regex_discord_message_url + regex_extra_url, url)
    data = base_url_match.groupdict()
    return {
        "base_author_id": int(data["base_author_id"]),
        "author_id": int(data["author_id"]),
        "extra_messages": [int(_id) for _id in data["extra_messages"].split(",")] if data["extra_messages"] else []
    }


def compose_embed(message: Message)-> Embed:
    if message.author.avatar:
        avatar_url = message.author.display_avatar.url
    else:
        avatar_url = None
    if message.guild.icon:
        icon_url = message.guild.icon.url
    else:
        icon_url = None
    embed = Embed(
        description=message.content, timestamp=message.created_at
    ).set_author(
        name=message.author.display_name, icon_url=avatar_url, url=message.jump_url
    ).set_footer(
        text=message.channel.name, icon_url=icon_url
    )
    if (
        message.attachments
        and (attachment:=message.attachments[0]).proxy_url
        and (attachment.content_type or '').startswith('image')
    ):
        embed.set_image(url=attachment.proxy_url)
    return embed
