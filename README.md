# dispander (Discord Message URL Expander)
DiscordのメッセージURLを検知して展開する機能を追加する、discord.py Bot拡張用ライブラリのforkです。

# 使い方

`python3 -m pip install dispander@git+https://github.com/hawk-tomy/dispander`

## extensionとして使用する場合

load_extensionで読み込んでください

```python
from discord.ext import commands

bot = commands.Bot(command_prefix='/')
bot.load_extension('dispander')
bot.run(token)
```

## 関数として使用する場合

on_message内のどこかで実行してください。

展開したメッセージを消去する機能を使用するには`on_raw_reaction_add`イベントでキーワード引数`payload`にRawReactionActionEventを指定してdelete_dispand関数を実行してください。

消去の際のリアクションを変更したい場合は環境変数`DELETE_REACTION_EMOJI`に絵文字を設定してください。

```python
import discord
from dispander import dispand, delete_dispand

client = discord.Client()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    await dispand(message)


@client.event
async def on_raw_reaction_add(payload):
    await delete_dispand(client, payload=payload)


client.run(token)
```
