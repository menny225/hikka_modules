__version__ = (1, 0, 0)


import logging
import time
import contextlib
import re

from typing import Union

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, DeleteMessagesRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, InviteToChannelRequest, EditAdminRequest
from telethon.tl.types import Message, PeerUser, ChatAdminRights

from .. import loader, utils

logger = logging.getLogger(__name__)


def format_(state: Union[bool, None]) -> str:
    if state is None:
        return "❔"

    return "✅" if state else "🚫 Not"


@loader.tds
class ABS(loader.Module):
    """Bans and delete incoming messages from spam-bots"""

    strings = {
        "name": "AntiBotSpam",
        "state": "⚔️ <b>AntiBotSpam is now {}</b>\n<i>Notify? - {}Delete dialog? - {}</i>",
        "ban":"🚫 @{} is BANNED! 🚫",
        "clear": "🗑️ List of users cleared!",
        "unbanned":"🕊️ Bot {} succesfully unbanned 🕊️",
        "unban": "ℹ️ Choose a message about blocking the bot",
        "args": "ℹ️ <b>Example usage: </b><code>.spamset 0 0</code>",
        "config": "😶‍🌫️ <b>Config saved</b>\n<i>Notify? - {}\nDelete dialog? - {}</i>",
        "_cmd_doc_spam": "Disable\\Enable Protection",
        "_cmd_doc_clear": "Clear user list",
        "_cmd_doc_unban": "Unblock BOT",
        "_cmd_doc_spamset": "<Report about the ban?> <Delete dialogue?> - in the format 1/0",
        "_cls_doc": "Blocks and deletes incoming messages from bots with which you did not start a dialogue",
    }

    strings_ru = {
        "state": "⚔️ <b>Текущее состояние AntiBotSpam: {}</b>\n<i>Сообщать о бане? - {}\nУдалять диалог? - {}</i>",
        "ban": "🚫 @{} is BANNED! 🚫",
        "clear": "🗑️ Список пользователей очищен!",
        "unbanned":"🕊️ Бот {} успешно разблокирован 🕊️",
        "unban": "ℹ️ Выберете сообщение о блокировке бота",
        "args": "ℹ️ <b>Пример: </b><code>.spamset 0 0</code>",
        "config": "😶‍🌫️ <b>Конфиг сохранен</b>\n<i>Сообщать о бане? - {}\nУдалять диалог? - {}</i>",
        "_cmd_doc_spam": "Выключить\\Включить защиту",
        "_cmd_doc_clear": "Очистить список пользователей",
        "_cmd_doc_unban": "Разблокировать бота",
        "_cmd_doc_spamset": "<Сообщать о бане?> <Удалять диалог?> - в формате 1/0",
        "_cls_doc": "Блокирует и удаляет входящие сообщения от ботов с которыми вы не начинали диалог",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(

        )



    async def client_ready(self, client, db):
        self._whitelist = self.get("whitelist", [])
        self._ratelimit = []
        self._ratelimit_timeout = 5 * 60
        self._ratelimit_threshold = 10

    async def on_dlmod(self, client, db):
        """Creating chat for logging"""
        result = await utils.asset_channel(
            self._client,
            "ABS",
            "ABS",
            silent=True,
            archive=True,
            avatar="https://ru.botostore.com/netcat_files/6/7/preview_153367_1618236665.jpg",
            _folder="hikka"
        )

        await self._client(InviteToChannelRequest(channel=result[0], users=[self.inline.bot.id]))
        await self._client(EditAdminRequest(
            channel=result[0],
            user_id=self.inline.bot.id,
            admin_rights=ChatAdminRights(
                change_info=True,
                edit_messages=True,
                post_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=True,
                anonymous=True,
                manage_call=True,
                other=True
            ),
            rank='Logger'
            )
        )
        self.set("state","true")
        self.set("notify", "true")
        self.set("delete", "true")
        self.set("chat_id", str(result[0].id))

    async def spamcmd(self, message: Message):
        """Toggle AntiBotSpam"""
        current = self.get("state", False)
        new = not current
        self.set("state", new)
        await utils.answer(
            message,
            self.strings("state").format(
                "on" if new else "off",
                "yes" if self.get("notify", False) else "no",
                "yes" if self.get("delete", False) else "no",
            ),
        )

    async def spamsetcmd(self, message: Message):
        """<Notify?> <Delete dialog?> - Configure AntiBotSpam - param are 1/0"""
        args = utils.get_args(message)
        if not args or len(args) != 2 or any(not _.isdigit() for _ in args):
            await utils.answer(message, self.strings("args"))
            return

        notify, delete = list(map(int, args))

        self.set("notify", notify)
        self.set("delete", delete)

        await utils.answer(
            message,
            self.strings("config").format(
                "yes" if notify else "no",
                "yes" if delete else "no",
            ),
        )





    async def unbancmd(self, message: Message):
        """Unbanning BOT"""
        if (await message.get_reply_message()):
            Reply = await message.get_reply_message()
            ID = re.findall("@\w*",str(Reply.message))

            await self._client(UnblockRequest(id=ID[0]))

            User = await self._client(GetFullUserRequest(id=ID[0]))
            if User.full_user.id in self._whitelist:
                self._whitelist.remove(User.full_user.id)

            await utils.answer(message, self.strings("unbanned").format(ID[0]))
            time.sleep(2)
            await Reply.delete()
            await message.delete()
        else:
            await utils.answer(message, self.strings("unban"))
            time.sleep(2)
            await message.delete()

    async def clearcmd(self, message: Message):
        """Clear db"""
        self._whitelist = []
        self._whitelist = list(set(self._whitelist))
        self.set("whitelist", self._whitelist)
        await utils.answer(message, self.strings("clear"))
        time.sleep(2)
        await message.delete()

    def _approve(self, user: int, reason: str = "unknown"):
        self._whitelist += [user]
        self._whitelist = list(set(self._whitelist))
        self.set("whitelist", self._whitelist)
        return

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            or not isinstance(message, Message)
            or not isinstance(message.peer_id, PeerUser)
            or not self.get("state", False)
            or utils.get_chat_id(message)
            in {
                777000,  # Telegram Notifications
                self._tg_id,  # Self
            }
        ):
            return

        cid = utils.get_chat_id(message)
        if cid in self._whitelist:
            return

        peer = (
            getattr(getattr(message, "sender", None), "username", None)
            or message.peer_id
        )

        first_message = (
            await self._client.get_messages(
                peer,
                limit=1,
                reverse=True,
            )
        )[0]

        with contextlib.suppress(ValueError):

            entity = await self._client.get_entity(peer)

            if (
                entity.bot
            ):
                if (first_message.sender_id == self._tg_id):
                    return self._approve(cid, "bot")
            else:
                return self._approve(cid, "ignore_users")

        self._ratelimit = list(
            filter(
                lambda x: x + self._ratelimit_timeout < time.time(),
                self._ratelimit,
            )
        )

        if len(self._ratelimit) < self._ratelimit_threshold:

            self._ratelimit += [round(time.time())]

        await self._client.send_read_acknowledge(cid) # Read message

        await self._client(BlockRequest(id=cid)) # Block user

        if self.get("delete", False):
            await self._client(
                DeleteHistoryRequest(peer=cid, just_clear=True, max_id=0)
            )

        self._approve(cid, "banned")

        if self.get("notify", False):
            dialog = await self._client.get_entity(peer)
            await self.inline.bot.send_message(f"-100{self.get('chat_id')}", self.strings("ban").format(dialog.username))