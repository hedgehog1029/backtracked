# backtracked

A python wrapper for the Dubtrack API.
Currently in alpha.

You can find docs [here](http://offbeatwit.ch/backtracked/build/index.html).

### Example

```python
from backtracked import Client, Presence, Message
import logging

c = Client()
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(name)s: %(message)s")

@c.event
async def on_ready():
    print("Logged in as {0.username}".format(c.user))
    await c.join_room("my-awesome-room")

@c.event
async def on_chat(message: Message):
    if message.content == "~online":
        await message.room.change_presence(Presence.enter)
    elif message.content == "~ping":
        await message.room.send_message("Pong!")

c.run(email="bot@example.com", password="my_bot_password")
```
