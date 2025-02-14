# dispander (Discord Message URL Expander)
DiscordのメッセージURLを検知して展開する機能を追加する、discord.py Bot拡張用ライブラリのforkです。
なお、一部内容を変更可能な`CustomizableDispander`が追加されています。

## 使い方

`python3 -m pip install dispander@git+https://github.com/hawk-tomy/dispander`

### extensionとして使用する場合

load_extensionで読み込んでください

```python
from discord import Intents
from discord.ext import commands

class Bot(commands.bot):
    async def setup_hook(self):
        await self.load_extension('dispander')

bot = Bot(command_prefix='/', intents=Intents.all())
bot.run(token)
```

### Cogとして使用する場合

`dispander.ExpandDiscordMessageFromUrlCog`を読み込んでください。

```python
from discord import Intents
from discord.ext import commands
from dispander import ExpandDiscordMessageFromUrlCog

class Bot(commands.bot):
    async def setup_hook(self):
        await self.add_cog(ExpandDiscordMessageFromUrlCog(self))

bot = Bot(command_prefix='/', intents=Intents.all())
bot.run(token)
```

### Dispanderクラスを直接用いる場合
```python
import discord
from dispander import Dispander

client = discord.Client(intents=discord.Intents.all())
dispander = Dispander(client)

@client.event
async def on_message(message):
    if message.author.bot:
        return
    await dispander.dispand(message)


@client.event
async def on_raw_reaction_add(payload):
    await dispander.delete_dispand(payload=payload)


client.run(token)
```

## CustomizableDispander

基本的なdipsnaderの動作はそのままに、展開後の埋め込みの内容の動的な変更を行えます。
なお、デフォルトで実行結果をキャッシュしています。

Message, Guild, Channel, Attachmentをそれぞれ独立して変更可能です。
- message
  - content
  - author
    - avatar (url)
    - name
- guild
  - icon url
- channel
  - name
- attachment
  - name
  - url(proxy url)

### 使い方
変更の対象ごとに、それぞれその対象を引数にとり、それぞれに合ったデータクラスを返す関数を定義し、`Customizer`の`set_*`に渡すことで設定が可能です。
それを`CustomizableDispander`に渡し、展開機能にはその`dispand`メソッドを、削除機能には`delete_dispand`メソッドを呼び出してください(それぞれの引数は[ここ](#dispanderクラスを直接用いる場合)を参照してください)。

以下の通りです。

```python
import discord
from dispander.customizable import *

async def message_customizer(msg: discord.Message)-> MessageCustomized:
    return MessageCustomized(
        content=msg.content * 2, # repeat message
        author_avatar_url=..., # Ellipsis mean, NOT REPLACE
        author_name="?"*len(msg.author.display_name), # user name replace to ???
    )

async def guild_customizer(guild: discord.Guild)-> GuildCustomized:
    return GuildCustomized(icon_url=None)
    # if you set `None`, dispander not set for dispand Embed.

async def channel_customizer(channel: GuildMessageableChannel)-> ChannelCustomized:
    return ChannelCustomized()
    # default value of *Customized class is Ellipsis.
    # but, it is same as not call `Customizer.set_*`.

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        customizer = Customizer(
        ).set_message(
            message_customizer
        ).set_guild(
            guild_customizer,
            enable_cache=False # if you want disable cache
        ).set_channel(
            channel_customizer
        )# .set_author()
        # if not call set_*, Customizer return default customizer that does nothing.

        self.dispander = CustomizableDispander(self, customizer)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.dispander.dispand(message)

    async def on_raw_reaction_add(self, payload):
        await self.dispander.delete_dispand(payload=payload)

bot = Bot()
bot.run(token)
```
