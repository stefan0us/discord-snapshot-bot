import io
import logging
import os
import re
import sys
import traceback
import uuid

import discord
from discord.ext.commands import Bot

from utils.playwright_helper import SnapshotHandler


class SnapshotBot(Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s",
                            stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.url_patten = re.compile(r'(?P<url>https?://[^\s]+)')
        self.snapshot_handler = SnapshotHandler()
        self.loop.create_task(self.snapshot_handler.get_task())

    async def on_ready(self):
        self.logger.info(f'discord server connected. [{self.user.name=}]')

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        await self.take_snapshot(message)

    async def take_snapshot(self, message: discord.Message):
        url_result = self.url_patten.search(message.content)
        if url_result:
            async with message.channel.typing():
                try:
                    result = await self.snapshot_handler.snapshot(url_result['url'])
                    await message.channel.send(
                        result['title'],
                        file=discord.File(
                            fp=io.BytesIO(result['content']),
                            filename=f"{uuid.uuid4()}.jpeg"),
                        reference=message
                    )
                except Exception as e:
                    self.logger.exception(e)
                    await message.channel.send(f'```\n{traceback.format_exc()}\n```', reference=message)


if __name__ == '__main__':
    client = SnapshotBot(command_prefix='')
    client.run(os.environ['TOKEN'])
