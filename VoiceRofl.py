__version__ = (1, 0, 0)

import io
import os
import time

from pydub import AudioSegment
from telethon.tl.custom import Message

from .. import loader, utils


@loader.tds
class VoiceRofl(loader.Module):
    """Saving and sendings voice-rofls"""

    strings = {
        "name": "VoiceRofl",
        "upload": "📤 Uploading...",
        "saved": "💾 Saved!",
        "exist": "🚫 Rofl alredy exist!",
        "unexist": "🚫 Rofl not finded!",
        "pick": "ℹ Reply voice!",
        "args": "ℹ Pick name!",
        "_cmd_doc_saverofl": "<Название> - Save rofl on channel",
        "_cmd_doc_rofl": "<Название> - Send rofl"

    }

    strings_ru = {
        "download": "📥 Скачиваю...",
        "upload": "📤 Выгружаю...",
        "saved": "💾 Сохранено!",
        "exist": "🚫 Рофл уже существует!",
        "unexist": "🚫 Рофл не найден!",
        "pick": "ℹ Выбери голосовое!",
        "args": "ℹ Укажи название!",
        "_cmd_doc_saverofl": "<Название> - Сохранить рофл на канал",
        "_cmd_doc_rofl": "<Название> - Отправить рофл"
    }

    async def on_dlmod(self, client, db):
        """Creating chat for logging"""
        result = await utils.asset_channel(
            client,
            "VoiceRofls",
            "VoiceRofls",
            silent=True,
            archive=True,
            avatar="https://raw.githubusercontent.com/menny225/hikka_modules/master/assets/VoicePic.png",
            _folder="hikka"
        )

    @staticmethod
    async def _delmes(self, message: Message):
        time.sleep(2)
        await message.delete()

    async def _check(self, name):
        cl = self.client.iter_messages('VoiceRofls')
        async for mess in cl:
            time.sleep(.1)
            if str(mess.message) == name:
                return mess

    async def _voice(self, message: Message):
        m = io.BytesIO()
        voice = await self.client.download_media(message=message.media)
        audio = AudioSegment.from_file(voice, "ogg")
        os.remove(voice)
        m.name = "voice.ogg"
        audio.split_to_mono()
        audio.export(m, format="ogg", codec="libopus", bitrate="64k")
        return m

    async def saveroflcmd(self, message: Message):
        reply = await message.get_reply_message()
        if reply:
            name = utils.get_args(message)
            if name:
                response = await self._check(name[0])
                if not response:
                    await utils.answer(message, self.strings("download"))
                    voice = await self._voice(reply)
                    await utils.answer(message, self.strings("upload"))
                    await self.client.send_file(
                        caption=str(name[0]), entity='VoiceRofls', file=voice, voice_note=True
                    )
                    await utils.answer(message, self.strings("saved"))
                    await self._delmes(message)
                else:
                    await utils.answer(message, self.strings("exist"))
                    await self._delmes(message)
            else:
                await utils.answer(message, self.strings("args"))
                await self._delmes(message)
        else:
            await utils.answer(message, self.strings("pick"))
            await self._delmes(message)

    async def roflcmd(self, message: Message):
        name = utils.get_args(message)
        if name:
            response = await self._check(name[0])
            if response:
                await utils.answer(message, self.strings("download"))
                voice = await self._voice(response)
                await utils.answer(message, self.strings("upload"))
                await message.client.send_file(
                    message.chat_id, file=voice, voice_note=True
                )
                await message.delete()
            else:
                await utils.answer(message, self.strings("unexist"))
                await self._delmes(message)
        else:
            await utils.answer(message, self.strings("args"))
            await self._delmes(message)
