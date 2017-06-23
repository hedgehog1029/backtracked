.. currentmodule:: backtracked

API Reference
=============

The following docs outline the classes involved in backtracked.

Client
------

.. autoclass:: Client
   :members:

Data Classes
------------

**These classes should never be constructed.** They are given to you in the various events and methods in the library.

.. IMPORTANT::
   Creating the data classes yourself **will result in pain and suffering.**

Room
^^^^

.. autoclass:: Room
   :members:

User
^^^^

.. autoclass:: User
   :members:

Member
^^^^^^

.. autoclass:: Member
   :members:

AuthenticatedUser
^^^^^^^^^^^^^^^^^

.. autoclass:: AuthenticatedUser
   :members:

Message
^^^^^^^

.. autoclass:: Message
   :members:

Song
^^^^

.. autoclass:: Song
   :members:

SongInfo
^^^^^^^^

.. autoclass:: SongInfo
   :members:

Helper Classes
--------------

These classes *can* be created by the user, and are used for supplying information to certain methods.

ProxyOptions
^^^^^^^^^^^^

.. autoclass:: ProxyOptions
   :members:

Enums
-----

Classes here extend python's builtin `Enum`_ class.
Some attributes use these objects, and some parameters take these objects.

.. _Enum: https://docs.python.org/3/library/enum.html

Presence
^^^^^^^^

.. autoclass:: Presence
   :undoc-members:

Role
^^^^

.. autoclass:: Role
   :undoc-members:

Utilities
---------

The `utils` module contains several helper functions useful for converting and extracting information
from various sources.

.. automodule:: backtracked.utils
   :members:
