__version__ = (1, 0, 1)

import io
import os
import time

from pydub import AudioSegment
from telethon.errors import MessageEmptyError
from telethon.tl.custom import Message

from .. import loader, utils


@loader.tds
class VoiceRofl(loader.Module):
    """Saving and sends voice-rofls"""

    strings = {
        "name": "VoiceRofl",
        "saved": "💾 Saved!",
        "exist": "🚫 Rofl already exist!",
        "unexist": "🚫 Rofl not found!",
        "empty": "ℹ Rofl list is empy!",
        "pick": "ℹ Reply voice!",
        "args": "ℹ Pick name!",
        "list": "ℹ Rofl list:",
    }

    strings_ru = {
        "saved": "💾 Сохранено!",
        "exist": "🚫 Рофл уже существует!",
        "unexist": "🚫 Рофл не найден!",
        "empty": "ℹ Список рофлов пуст!",
        "pick": "ℹ Выбери голосовое!",
        "args": "ℹ Укажи название!",
        "list": "ℹ Список рофлов:",
        "_cmd_doc_roflsave": "<Голосовое><Название> - Сохранить рофл на канал",
        "_cmd_doc_rofl": "<Название> - Отправить рофл",
        "_cmd_doc_rofllist": "Список рофлов",
        "_cmd_doc_rofldel": "<Название> - Удалить рофл",
        "_cls_doc": "Сохраняет и отправляет войс-рофлы",
    }

    async def on_dlmod(self, client, db):
        """Creating chat for rofls"""
        await utils.asset_channel(
            client,
            "VoiceRofls",
            "VoiceRofls",
            silent=True,
            archive=True,
            avatar="https://raw.githubusercontent.com/menny225/hikka_modules/master/assets/VoicePic.png",
            _folder="hikka"
        )

    @staticmethod
    async def _delmes(message: Message, text: str):
        await utils.answer(message, text)
        time.sleep(2)
        await message.delete()

    async def _check(self, name):
        cl = self.client.iter_messages('VoiceRofls')
        async for mess in cl:
            time.sleep(.1)
            if str(mess.message) == name:
                return mess

    async def roflsavecmd(self, message: Message):
        """<Voice><Name> - Save rofl to channel"""
        reply = await message.get_reply_message()
        if reply:
            name = utils.get_args_raw(message)
            if name:
                response = await self._check(name)
                if not response:
                    reply.text = name
                    await self.client.send_message(
                        entity='VoiceRofls',
                        message=reply,
                    )
                    await self._delmes(message, self.strings("saved"))
                else:
                    await self._delmes(message, self.strings("exist"))
            else:
                await self._delmes(message, self.strings("args"))
        else:
            await self._delmes(message, self.strings("pick"))

    async def roflcmd(self, message: Message):
        """<Reply: optional><Name> - Send rofl"""
        reply = await message.get_reply_message()
        name = utils.get_args_raw(message)
        if name:
            response = await self._check(name)
            if response:
                await message.delete()
                response.text = ""
                await self.client.send_message(
                    entity=message.chat,
                    message=response,
                    reply_to=reply,
                )
            else:
                await self._delmes(message, self.strings("unexist"))
        else:
            await self._delmes(message, self.strings("args"))

    async def rofllistcmd(self, message: Message):
        """Show rofl list"""
        result = self.strings("list")
        try:
            cl = self.client.iter_messages('VoiceRofls', reverse=True, offset_id=1)
            async for mess in cl:
                link = await utils.get_message_link(mess)
                result += f'\n<a href="{link}">{mess.text}</a>'
            await utils.answer(message, result)
        except MessageEmptyError:
            await self._delmes(message, self.strings("empty"))

    async def rofldelcmd(self, message: Message):
        """<Name> - Delete rofl from channel"""
        name = utils.get_args_raw(message)
        mess = await self._check(name)
        if mess:
            await self.client.delete_messages(mess.peer_id, [mess.id])
        else:
            await self._delmes(message, self.strings("unexist"))
