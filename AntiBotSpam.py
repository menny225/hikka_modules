__version__ = (1, 0, 1)


import logging
import time
import contextlib
import re

from typing import Union

from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import DeleteHistoryRequest, SendMessageRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import  InviteToChannelRequest, EditAdminRequest
from telethon.tl.types import Message, PeerUser, ChatAdminRights

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

        "settings": "⚙ Settings ⚙",
        "notify": "📩 Report about the ban: {}",
        "del": "🗑 Delete dialogue: {}",
        "close": "🔻 Close 🔻",

        "state": "⚔ <b>AntiBotSpam is now: {}</b>\n<i>Notify? - {}Delete dialog? - {}</i>",
        "ban":"🚫 @{} is BANNED! 🚫",
        "clear": "🗑 List of users cleared!",
        "unbanned": "🕊 Bot {} succesfully unbanned 🕊",
        "unban": "ℹ Choose a message about blocking the bot",
        "config": "😶‍🌫️ <b>Config saved</b>\n<i>Notify? - {}\nDelete dialog? - {}</i>",
        "_cmd_doc_spam": "Disable\\Enable Protection",
        "_cmd_doc_clear": "Clear user list",
        "_cmd_doc_unban": "Unblock BOT",
        "_cmd_doc_spamset": "MOD Config",
        "_cls_doc": "Blocks and deletes incoming messages from bots with which you did not start a dialogue",
    }

    strings_ru = {
        "settings": "⚙ Настройки ⚙",
        "notify": "📩 Сообщать о бане: {}",
        "del": "🗑 Удалять диалог: {}",
        "close": "🔻 Закрыть 🔻",

        "state": "⚔ <b>Текущее состояние AntiBotSpam: {}</b>\n<i>Сообщать о бане? - {}\nУдалять диалог? - {}</i>",
        "ban": "🚫 @{} is BANNED! 🚫",
        "clear": "🗑 Список пользователей очищен!",
        "unbanned": "🕊 Бот {} успешно разблокирован 🕊",
        "unban": "ℹ Выберете сообщение о блокировке бота",
        "config": "😶‍🌫️ <b>Конфиг сохранен</b>\n<i>Сообщать о бане? - {}\nУдалять диалог? - {}</i>",
        "_cmd_doc_spam": "Выключить\\Включить защиту",
        "_cmd_doc_clear": "Очистить список пользователей",
        "_cmd_doc_unban": "Разблокировать бота",
        "_cmd_doc_spamset": "Конфигурация модуля",
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
                anonymous=True,
                other=True
            ),
            rank='Logger'
            )
        )

        self.set("chat_id", f"-100{str(result[0].id)}")

    async def client_ready(self, client, db):
        self._chat_id = self.get("chat_id")
        self._whitelist = self.get("whitelist", [])
        self._state = self.get("state",False)
        self._notify = self.get("notify",False)
        self._delete = self.get("delete", False)

    async def spamcmd(self, message: Message):
        """Toggle AntiBotSpam"""
        self._state = not self._state
        self.set("state", self._state)
        await utils.answer(
            message,
            self.strings("state").format(
                "on" if self._state else "off",
                format_(self.get("notify")),
                format_(self.get("delete")),
            ),
        )

    async def spamsetcmd(self, message: Message):
        await self.inline.form(
            text= self.strings("settings"),
            message=message,
            reply_markup=[
                [
                    {
                        "text": self.strings("notify").format(format_(self._notify)),
                        "callback": self._setter,
                        "kwargs": {"param": "notify"},
                    }
                ],
                [
                    {
                        "text": self.strings("del").format(format_(self._delete)),
                        "callback": self._setter,
                        "kwargs": {"param": "delete"},
                    }
                ],
                [
                    {
                        "text": self.strings("close"),
                        "action": "close",
                    }
                ],
            ],
            force_me= True,
            ttl=60,
            silent=True,  # optional: Send form silently
        )

    async def _setter(self, call: InlineCall, param: str):
        """Changing settiings"""
        if param == "notify":
            self._notify = not self._notify
            self.set("notify", self._notify)
        else:
            self._delete = not self._delete
            self.set("delete", self._delete)

        await call.edit(
            text= self.strings("settings"),
            reply_markup=[
                [
                    {
                        "text": self.strings("notify").format(format_(self._notify)),
                        "callback": self._setter,
                        "kwargs": {"param": "notify"},
                    }
                ],
                [
                    {
                        "text": self.strings("del").format(format_(self._delete)),
                        "callback": self._setter,
                        "kwargs": {"param": "delete"},
                    }
                ],
                [
                    {
                        "text": self.strings("close"),
                        "action": "close",
                    }
                ],
            ],
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
                if (first_message.sender_id == self._tg_id):
                    return self._approve(cid, "bot")
            else:
                return self._approve(cid, "ignore_users")

        await self._client.send_read_acknowledge(cid) # Read message

        await self._client(BlockRequest(id=cid)) # Block user

        if self._delete:
            await self._client(
                DeleteHistoryRequest(peer=cid, just_clear=True, max_id=0)
            )

        self._approve(cid, "banned")

        if self._notify:
            dialog = await self._client.get_entity(peer)
            await self.inline.bot.send_message(self._chat_id, self.strings("ban").format(dialog.username))