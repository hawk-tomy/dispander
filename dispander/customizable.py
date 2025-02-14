from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, TypeAlias

from discord import DMChannel, GroupChannel, PartialMessageable
from discord.utils import maybe_coroutine

from .core import Dispander

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from types import EllipsisType
    from typing import Any, Concatenate, ParamSpec, Self, TypeVar

    from discord import Asset, Attachment, Client, Colour, Emoji, Guild, Member, Message, PartialEmoji, User
    from discord.abc import MessageableChannel
    from discord.mixins import Hashable

    P = ParamSpec('P')
    Id = TypeVar('Id', bound=Hashable)
    T = TypeVar('T')
    U = TypeVar('U')
    Optional_: TypeAlias = EllipsisType | None | T


__all__ = (
    'AttachmentCustomized',
    'ChannelCustomized',
    'CustomizableDispander',
    'Customizer',
    'GuildCustomized',
    'MessageCustomized',
)


@dataclass
class MessageCustomized:
    """Customized Message Data."""

    content: Optional_[str] = ...
    author_avatar_url: Optional_[str] = ...
    author_name: Optional_[str] = ...


@dataclass
class GuildCustomized:
    """Customized Guild Data."""

    icon_url: Optional_[str] = ...


@dataclass
class ChannelCustomized:
    """Customized Channel Data."""

    name: Optional_[str] = ...


@dataclass
class AttachmentCustomized:
    """Customized Attachment Data."""

    content_type: Optional_[str] = ...
    proxy_url: Optional_[str] = ...


if TYPE_CHECKING:
    MaybeCoroutineFunc = Callable[[T], Awaitable[U]] | Callable[[T], U]
    GuildCustomizerFunc = MaybeCoroutineFunc[Guild, GuildCustomized]
    ChannelCustomizerFunc = MaybeCoroutineFunc[MessageableChannel, ChannelCustomized]
    MessageCustomizerFunc = MaybeCoroutineFunc[Message, MessageCustomized]
    AttachmentCustomizerFunc = MaybeCoroutineFunc[Attachment, AttachmentCustomized]


class IconMock(NamedTuple):
    url: str | None


class UserMock(NamedTuple):
    user: User | Member
    avatar: Asset | IconMock | None
    display_avatar: Asset | IconMock | None
    display_name: str

    def __getattribute__(self, name: str) -> Any:  # noqa: ANN401
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.user, name)


class GuildMock(NamedTuple):
    guild: Guild
    icon: IconMock | None

    def __getattribute__(self, name: str) -> Any:  # noqa: ANN401
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.guild, name)


def get_user(user: User | Member, icon: Optional_[str], name: Optional_[str]) -> EllipsisType | UserMock:
    if icon is ... and name is ...:
        return ...

    icon_ = user.avatar if icon is ... else icon if icon is None else IconMock(icon)
    name_ = user.display_name if name is ... or name is None else name

    return UserMock(user, icon_, icon_, name_)


def get_guild(guild: Guild, value: Optional_[str]) -> EllipsisType | GuildMock:
    if value is not ...:
        icon = None
        if value is not None:
            icon = IconMock(value)
        return GuildMock(guild, icon)
    return ...


def _setter(target: Any, name: str, value: Any) -> None:  # noqa: ANN401
    if value is not ...:
        setattr(target, name, value)


def cache(func: Callable[Concatenate[Id, P], Awaitable[T] | T]) -> Callable[Concatenate[Id, P], Awaitable[T]]:
    cache: dict[int, T] = {}

    async def inner(value: Id, *args: P.args, **kwargs: P.kwargs) -> T:
        if value.id in cache:
            return cache[value.id]
        returned = await maybe_coroutine(func, value, *args, **kwargs)
        cache[value.id] = returned
        return returned

    return inner  # type: ignore[return-value]


class Customizer:
    """Setting customizer functions for each component with optional caching."""

    __message: MessageCustomizerFunc
    __guild: GuildCustomizerFunc
    __channel: ChannelCustomizerFunc
    __attachment: AttachmentCustomizerFunc

    @property
    def _message(self) -> MessageCustomizerFunc:
        try:
            return self.__message
        except AttributeError:

            def inner(_: Message) -> MessageCustomized:
                return MessageCustomized()

            self.__message = inner
            return inner

    @_message.setter
    def _message(self, customizer: MessageCustomizerFunc) -> None:
        self.__message: MessageCustomizerFunc = customizer

    def set_message(self, customizer: MessageCustomizerFunc, *, enable_cache: bool = True) -> Self:
        """Sets the message customizer function.

        Args:
            customizer (MessageCustomizerFunc): A function that customizes a message.
            enable_cache (bool, optional): If True, the message will be cached. Defaults to True.

        Returns:
            Self: The class instance to allow for fluent-style chaining.
        """
        if enable_cache:
            self._message = cache(customizer)
        else:
            self._message = customizer
        return self

    @property
    def _guild(self) -> GuildCustomizerFunc:
        try:
            return self.__guild
        except AttributeError:

            def inner(_: Guild) -> GuildCustomized:
                return GuildCustomized()

            self.__guild = inner
            return inner

    @_guild.setter
    def _guild(self, customizer: GuildCustomizerFunc) -> None:
        self.__guild = customizer

    def set_guild(self, customizer: GuildCustomizerFunc, *, enable_cache: bool = True) -> Self:
        """Sets the guild customizer function.

        Parameters:
            customizer (GuildCustomizerFunc): A function that customizes a guild.
            enable_cache (bool, optional): If True, caches the customizer function. Defaults to True.

        Returns:
            Self: The class instance to allow for fluent-style chaining.
        """
        if enable_cache:
            self._guild = cache(customizer)
        else:
            self._guild = customizer
        return self

    @property
    def _channel(self) -> ChannelCustomizerFunc:
        try:
            return self.__channel
        except AttributeError:

            def inner(_: MessageableChannel) -> ChannelCustomized:
                return ChannelCustomized()

            self.__channel = inner
            return inner

    @_channel.setter
    def _channel(self, customizer: ChannelCustomizerFunc) -> None:
        self.__channel = customizer

    def set_channel(self, customizer: ChannelCustomizerFunc, *, enable_cache: bool = True) -> Self:
        """Sets the channel customizer function.

        Parameters:
            customizer (ChannelCustomizerFunc): A function that customizes a channel.
            enable_cache (bool, optional): If True, caches the customizer function. Defaults to True.

        Returns:
            Self: The class instance to allow for fluent-style chaining.
        """
        if enable_cache:
            self._channel = cache(customizer)
        else:
            self._channel = customizer
        return self

    @property
    def _attachment(self) -> AttachmentCustomizerFunc:
        try:
            return self.__attachment
        except AttributeError:

            def inner(_: Attachment) -> AttachmentCustomized:
                return AttachmentCustomized()

            self.__attachment = inner
            return inner

    @_attachment.setter
    def _attachment(self, customizer: AttachmentCustomizerFunc) -> None:
        self.__attachment = customizer

    def set_attachment(self, customizer: AttachmentCustomizerFunc, *, enable_cache: bool = True) -> Self:
        """Sets the Attachment customizer function.

        Parameters:
            customizer (AttachmentCustomizerFunc): A function that customizes a Attachment.
            enable_cache (bool, optional): If True, caches the customizer function. Defaults to True.

        Returns:
            Self: The class instance to allow for fluent-style chaining.
        """
        if enable_cache:
            self._attachment = cache(customizer)
        else:
            self._attachment = customizer
        return self


class CustomizableDispander(Dispander):
    """A class that extends Dispander to allow customization by customizers."""

    def __init__(
        self,
        bot: Client,
        customizer: Customizer,
        delete_reaction_emoji: None | str | Emoji | PartialEmoji = None,
        embed_color: None | int | Colour = None,
    ) -> None:
        super().__init__(bot, delete_reaction_emoji, embed_color)
        self.customizer = customizer

    async def _extract_message(self, message: Message) -> list[Message]:
        messages = await super()._extract_message(message)
        customized_messages: list[Message] = []
        for message_ in messages:
            assert message_.guild is not None
            assert not isinstance(message_.channel, (DMChannel, GroupChannel, PartialMessageable))  # noqa: UP038

            msg = await maybe_coroutine(self.customizer._message, message_)
            guild = await maybe_coroutine(self.customizer._guild, message_.guild)
            channel = await maybe_coroutine(self.customizer._channel, message_.channel)

            attachments: list[AttachmentCustomized] = [
                await maybe_coroutine(self.customizer._attachment, attachment) for attachment in message_.attachments
            ]

            customized_messages.append(self._replace_message(message_, msg, guild, channel, attachments))

        return customized_messages

    def _replace_message(
        self,
        msg: Message,
        extra_msg: MessageCustomized,
        guild: GuildCustomized,
        channel: ChannelCustomized,
        attachments: list[AttachmentCustomized],
    ) -> Message:
        _setter(msg, 'content', extra_msg.content)
        _setter(
            msg,
            'author',
            get_user(msg.author, extra_msg.author_avatar_url, extra_msg.author_name),
        )

        assert msg.guild is not None
        _setter(msg, 'guild', get_guild(msg.guild, guild.icon_url))

        _setter(msg.channel, 'name', channel.name)

        for attachment, extra in zip(msg.attachments, attachments, strict=False):
            _setter(attachment, 'content_type', extra.content_type)
            _setter(attachment, 'proxy_url', extra.proxy_url)

        return msg
