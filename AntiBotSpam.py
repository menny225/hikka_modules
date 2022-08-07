__version__ = (1, 0, 3)

import logging
import time
import contextlib
import re

from typing import Union
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest, EditAdminRequest
from telethon.tl.types import PeerUser, ChatAdminRights
from telethon.tl.custom import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


def format_(state: Union[bool, None]) -> str:
    if state is None:
        return "❔"

    return "✅" if state else "🚫"


@loader.tds
class ABS(loader.Module):
    """Bans and delete incoming messages from spam-bots"""

    strings = {
        "name": "AntiBotSpam",
        "settings": "⚙ <b>Settings:</b>",
        "notify": "📩 Report about the ban: {}",
        "del": "🗑 Delete dialogue: {}",
        "close": "🔻 Close 🔻",
        "state": "⚔ AntiBotSpam Activity: {}",
        "ban": "🚫 @{} is BANNED! 🚫",
        "clear": "🗑 List of bots cleared!",
        "unbanned": "🕊 Bot {} unbanned 🕊",
        "unban": "ℹ Choose a message about blocking the bot",
        "_cmd_doc_clear": "Clear user list",
        "_cmd_doc_unban": "Unblock BOT",
        "_cmd_doc_spam": "MOD Config",
        "_cls_doc": "Blocks and deletes incoming messages from bots with which you did not start a dialogue",
    }

    strings_ru = {
        "settings": "⚙ <b>Настройки:</b>",
        "notify": "📩 Сообщать о бане: {}",
        "del": "🗑 Удалять диалог: {}",
        "close": "🔻 Закрыть 🔻",
        "state": "⚔ Активность AntiBotSpam: {}",
        "ban": "🚫 @{} is BANNED! 🚫",
        "clear": "🗑 Список заблокированных очищен!",
        "unbanned": "🕊 Бот {} разблокирован 🕊",
        "unban": "ℹ Выберете сообщение о блокировке бота",
        "_cmd_doc_clear": "Очистить список пользователей",
        "_cmd_doc_unban": "Разблокировать бота",
        "_cmd_doc_spam": "Конфигурация модуля",
        "_cls_doc": "Блокирует и удаляет входящие сообщения от ботов с которыми вы не начинали диалог",
    }

    async def on_dlmod(self, client, db):
        """Creating chat for logging"""
        result = await utils.asset_channel(
            self._client,
            "ABS",
            "ABS",
            silent=True,
            archive=True,
            avatar="https://raw.githubusercontent.com/menny225/hikka_modules/master/assets/ASBPic.jpg",
            _folder="hikka"
        )

        await self._client(InviteToChannelRequest(channel=result[0], users=[self.inline.bot.id]))
        await self._client(EditAdminRequest(
            channel=result[0],
            user_id=self.inline.bot.id,
            admin_rights=ChatAdminRights(
                edit_messages=True,
                post_messages=True,
                delete_messages=True,
            ),
            rank='Logger'
        )
        )

        self.set("chat_id", f"-100{str(result[0].id)}")

    def form(self):
        return [
            [{
                "text": self.strings("state").format(format_(self._state)),
                "callback": self._setter, "kwargs": {"param": "state"},
            }],
            [{
                "text": self.strings("notify").format(format_(self._notify)),
                "callback": self._setter, "kwargs": {"param": "notify"},
            },
                {
                    "text": self.strings("del").format(format_(self._delete)),
                    "callback": self._setter, "kwargs": {"param": "delete"},
                }],
            [{
                "text": self.strings("close"),
                "action": "close",
            }], ]

    async def client_ready(self, client, db):
        self._chat_id = self.get("chat_id")
        self._whitelist = self.get("whitelist", [])
        self._blacklist = self.get("blacklist", [])
        self._state = self.get("state", False)
        self._notify = self.get("notify", False)
        self._delete = self.get("delete", False)

    async def spamcmd(self, message: Message):
        await self.inline.form(
            text=self.strings('settings'),
            photo='https://raw.githubusercontent.com/menny225/hikka_modules/master/assets/Settings.png',
            message=message,
            reply_markup=self.form(),
            force_me=True,
            ttl=10*60,
        )

    async def _setter(self, call: InlineCall, param: str):
        """Changing settiings"""
        if param == "notify":
            self._notify = not self._notify
            self.set("notify", self._notify)
        elif param == "delete":
            self._delete = not self._delete
            self.set("delete", self._delete)
        else:
            self._state = not self._state
            self.set("state", self._state)

        await call.edit(
            text=self.strings('settings'),
            reply_markup=self.form(),
            force_me=True,
        )

    async def unbancmd(self, message: Message):
        """Unbanning BOT"""
        if await message.get_reply_message():
            reply = await message.get_reply_message()
            identy = re.findall(r'@\w*', str(reply.message))

            await self._client(UnblockRequest(id=identy[0]))

            user = await self._client(GetFullUserRequest(id=identy[0]))
            if user.full_user.id in self._blacklist:
                self._blacklist.remove(user.full_user.id)

            await utils.answer(message, self.strings("unbanned").format(identy[0]))
            time.sleep(2)
            await reply.delete()
            await message.delete()
        else:
            await utils.answer(message, self.strings("unban"))

    async def clearcmd(self, message: Message):
        """Clear db"""
        self.set("blacklist", [])
        await utils.answer(message, self.strings("clear"))
        time.sleep(2)
        await message.delete()

    def _approve(self, user: int):
        self._whitelist += [user]
        self._whitelist = list(set(self._whitelist))
        self.set("whitelist", self._whitelist)
        return

    async def _block(self, user):
        self._blacklist += [user]
        self._blacklist = list(set(self._blacklist))
        self.set("blacklist", self._blacklist)

        await self._client.send_read_acknowledge(user)  # Read message
        await self._client(BlockRequest(id=user))  # Block user

        if self._delete:
            await self._client(DeleteHistoryRequest(peer=user, just_clear=True, max_id=0))

        if self._notify:
            dialog = await self._client.get_entity(user)
            await self.inline.bot.send_message(self._chat_id, self.strings("ban").format(dialog.username))

        return

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            or not isinstance(message, Message)
            or not isinstance(message.peer_id, PeerUser)
            or not self.get("state", False)
            or utils.get_chat_id(message)
            in {
                1271266957,  # @replies
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
                if first_message.sender_id == self._tg_id:
                    return self._approve(cid)
            else:
                return self._approve(cid)

        await self._block(cid)
