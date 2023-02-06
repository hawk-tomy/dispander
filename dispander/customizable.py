from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from discord import DMChannel, GroupChannel, PartialMessageable, TextChannel, Thread, VoiceChannel
from discord.utils import maybe_coroutine

from .core import Dispander

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import Any, Optional, TypeVar, Union

    from discord import Asset, Attachment, Client, Colour, Emoji, Guild, Member, Message, PartialEmoji, User
    from discord.mixins import Hashable
    from typing_extensions import Concatenate, ParamSpec, Self

    P = ParamSpec('P')
    Id = TypeVar('Id', bound=Hashable)
    T = TypeVar('T')
    U = TypeVar('U')
    EllipsisType = type(...)
    Optional_ = Union[EllipsisType, None, T]


__all__ = (
    'MessageCustomized',
    'GuildCustomized',
    'ChannelCustomized',
    'AttachmentCustomized',
    'Customizer',
    'CustomizableDispander',
)

if TYPE_CHECKING:
    __all__ += ('GuildMessageableChannel',) # type: ignore


@dataclass
class MessageCustomized:
    content: Optional_[str]=...
    author_avatar_url: Optional_[str]=...
    author_name: Optional_[str]=...


@dataclass
class GuildCustomized:
    icon_url: Optional_[str]=...


@dataclass
class ChannelCustomized:
    name: Optional_[str]=...


@dataclass
class AttachmentCustomized:
    content_type: Optional_[str]=...
    proxy_url: Optional_[str]=...


if TYPE_CHECKING:
    GuildMessageableChannel = Union[TextChannel, VoiceChannel, Thread]
    MaybeCoroutineFunc = Union[Callable[[T], Awaitable[U]], Callable[[T], U]]
    GuildCustomizerFunc = MaybeCoroutineFunc[Guild, GuildCustomized]
    ChannelCustomizerFunc = MaybeCoroutineFunc[GuildMessageableChannel, ChannelCustomized]
    MessageCustomizerFunc = MaybeCoroutineFunc[Message, MessageCustomized]
    AttachmentCustomizerFunc = MaybeCoroutineFunc[Attachment, AttachmentCustomized]


class IconMock(NamedTuple):
    url: Optional[str]


class UserMock(NamedTuple):
    user: Union[User, Member]
    avatar: Union[Asset, IconMock, None]
    display_avatar: Union[Asset, IconMock, None]
    display_name: str

    def __getattribute__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.user, name)


class GuildMock(NamedTuple):
    guild: Guild
    icon: Optional[IconMock]

    def __getattribute__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.guild, name)


def get_user(user: Union[User, Member], icon: Optional_[str], name: Optional_[str])-> Union[EllipsisType, UserMock]:
    if icon is ... and name is ...:
        return ...

    if icon is ...:
        icon_ = user.avatar
    else:
        icon_ = icon if icon is None else IconMock(icon) # type: ignore

    if name is ... or name is None:
        name_ = user.display_name
    else:
        name_: str= name # type: ignore

    return UserMock(user, icon_, icon_, name_)


def get_guild(guild: Guild, value: Optional_[str])-> Union[EllipsisType, GuildMock]:
    if value is not ...:
        icon = None
        if value is not None:
            icon = IconMock(value) # type: ignore
        return GuildMock(guild, icon)
    return ...


def setter(target: Any, name: str, value: Any):
    if value is not ...:
        setattr(target, name, value)


def cache(
    func: Callable[Concatenate[Id, P], Union[Awaitable[T], T]]
)-> Callable[Concatenate[Id, P], Awaitable[T]]:
    cache: dict[int, T]= {}

    async def inner(value: Id, *args: P.args, **kwargs: P.kwargs):
        if value.id in cache:
            return cache[value.id]
        returned = await maybe_coroutine(func, value, *args, **kwargs)
        cache[value.id] = returned
        return returned

    return inner


class Customizer:
    @property
    def message(self)-> MessageCustomizerFunc:
        try:
            return self.__message
        except Exception:
            def inner(msg: Message)-> MessageCustomized:
                return MessageCustomized()
            self.__message = inner
            return inner

    @message.setter
    def message(self, customizer: MessageCustomizerFunc):
        self.__message: MessageCustomizerFunc= customizer

    def set_message(self, customizer: MessageCustomizerFunc, *, enable_cache: bool=True)-> Self:
        if enable_cache:
            self.message = cache(customizer)
        else:
            self.message = customizer
        return self

    @property
    def guild(self)-> GuildCustomizerFunc:
        try:
            return self.__guild
        except Exception:
            def inner(guild: Guild)-> GuildCustomized:
                return GuildCustomized()
            self.__guild = inner
            return inner

    @guild.setter
    def guild(self, customizer: GuildCustomizerFunc):
        self.__guild = customizer

    def set_guild(self, customizer: GuildCustomizerFunc, *, enable_cache: bool=True)-> Self:
        if enable_cache:
            self.guild = cache(customizer)
        else:
            self.guild = customizer
        return self

    @property
    def channel(self)-> ChannelCustomizerFunc:
        try:
            return self.__channel
        except Exception:
            def inner(channel: GuildMessageableChannel)-> ChannelCustomized:
                return ChannelCustomized()
            self.__channel = inner
            return inner

    @channel.setter
    def channel(self, customizer: ChannelCustomizerFunc):
        self.__channel = customizer

    def set_channel(self, customizer: ChannelCustomizerFunc, *, enable_cache: bool=True)-> Self:
        if enable_cache:
            self.channel = cache(customizer)
        else:
            self.channel = customizer
        return self

    @property
    def attachment(self)-> AttachmentCustomizerFunc:
        try:
            return self.__attachment
        except Exception:
            def inner(attach: Attachment)-> AttachmentCustomized:
                return AttachmentCustomized()
            self.__attachment = inner
            return inner

    @attachment.setter
    def attachment(self, customizer: AttachmentCustomizerFunc):
        self.__attachment = customizer

    def set_attachment(self, customizer: AttachmentCustomizerFunc, *, enable_cache: bool=True)-> Self:
        if enable_cache:
            self.attachment = cache(customizer)
        else:
            self.attachment = customizer
        return self


class CustomizableDispander(Dispander):
    def __init__(
        self,
        bot: Client,
        customizer: Customizer,
        delete_reaction_emoji: Union[None, str, Emoji, PartialEmoji] = None,
        embed_color: Union[None, int, Colour] = None,
    ):
        super().__init__(bot, delete_reaction_emoji, embed_color)
        self.customizer = customizer

    async def extract_message(self, message: Message) -> list[Message]:
        messages = await super().extract_message(message)
        customized_messages: list[Message]= []
        for message in messages:
            assert message.guild is not None
            assert not isinstance(message.channel, (DMChannel, GroupChannel, PartialMessageable))

            msg = await maybe_coroutine(self.customizer.message, message)
            guild = await maybe_coroutine(self.customizer.guild, message.guild)
            channel = await maybe_coroutine(self.customizer.channel, message.channel)

            attachments: list[AttachmentCustomized] = []
            for attachment in message.attachments:
                attachments.append(await maybe_coroutine(self.customizer.attachment, attachment))

            customized_messages.append(
                self.replace_message(message, msg, guild, channel, attachments)
            )

        return customized_messages

    def replace_message(
        self,
        msg: Message,
        extra_msg: MessageCustomized,
        guild: GuildCustomized,
        channel: ChannelCustomized,
        attachments: list[AttachmentCustomized],
    )-> Message:
        setter(msg, 'content', extra_msg.content)
        setter(msg, 'author', get_user(msg.author, extra_msg.author_avatar_url, extra_msg.author_name))

        assert msg.guild is not None
        setter(msg, 'guild', get_guild(msg.guild, guild.icon_url))

        setter(msg.channel, 'name', channel.name)

        for attachment, extra in zip(msg.attachments, attachments):
            setter(attachment, 'content_type', extra.content_type)
            setter(attachment, 'proxy_url', extra.proxy_url)

        return msg
