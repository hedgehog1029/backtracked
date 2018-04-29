.. currentmodule:: backtracked

Event Reference
===============

Through the :meth:`Client.event` decorator, you can subscribe to realtime events that the library dispatches.
This page lists the various events and their parameters.

Global Events
-------------

.. function:: on_ready()

    Called when the websocket connection was successfully established.
    Usually this call is used exclusively for joining rooms.

.. function:: on_joined_room(room)

    Emitted when a room is successfully joined.

    :param room: :class:`Room` that was joined in this event.

Room Events
-----------

.. function:: on_member_presence(room, user)

    Emitted when a user in a room changes presence.

    :param room: :class:`Room` that this event occurred in.
    :param user: :class:`User` that changed presence.

.. function:: on_chat(message)

    Emitted when a user sends a chat message in a joined room.
    You can access the room and user via fields on the :class:`Message` object.

    :param message: :class:`Message` that was received.

.. function:: on_chat_delete(message)

    Emitted when a message is deleted.
    This does not remove the message from the local cache.
    :attr:`Message.deleted` will be True.

    :param message: :class:`Message` which was deleted.

.. function:: on_dub(song, user, dubtype)

    Emitted when a user "dubs" a song. (In practice, this is always the current song.)
    You can get the type of the dub via the :data:`dubtype` parameter.

    :param song: :class:`Song` which was dubbed.
    :param user: :class:`User` who dubbed.
    :param dubtype: :class:`str` representing the type of dub in this event.

.. function:: on_playlist_song_add(song)

    Emitted when a new song is added to the current room queue.

    :param song: :class:`Song` object representing the item that was added.

.. function:: on_member_join(member)

    Emitted when a user joins a room.

    :param member: :class:`Member` object representing the user's room state.

.. function:: on_member_update(member)

    Emitted when a member of a room changes state in some way.

    :param member: :class:`Member` that changed state.

User Events
-----------

When subscribed to user rooms via :meth:`User.open_conversation`, you can receive user-specific events.

.. function:: on_private_message(conversation)

    Emitted when a user sends you a private message.
    Unlike :func:`on_chat`, this does not fire for the connected client's messages.

    :param conversation: :class:`Conversation` which the new message was sent in.