import io
import logging
import os
import re
import sys
import traceback
import uuid

import discord
from discord.ext.commands import Bot

from utils.customized_snapshot_handler import CustomizedSnapshotHandler


class SnapshotBot(Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s",
                            stream=sys.stdout, level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.url_patten = re.compile(r'(?P<url>https?://[^\s]+)')
        self.snapshot_handler = CustomizedSnapshotHandler()
        self.loop.create_task(self.snapshot_handler.get_task())

    async def on_ready(self):
        self.logger.info(f'discord server connected. [{self.user.name=}]')

    async def on_message(self, message):
        if message.author == self.user:
            return
        await self.take_snapshot(message)

    async def take_snapshot(self, message):
        url_result = self.url_patten.search(message.content)
        if url_result:
            async with message.channel.typing():
                try:
                    snapshot_id = uuid.uuid4()
                    await message.channel.send(file=discord.File(
                        fp=io.BytesIO(await self.snapshot_handler.snapshot(url_result['url'])),
                        filename=f"{snapshot_id}.jpeg"),
                        reference=message)
                except Exception as e:
                    self.logger.exception(e)
                    await message.channel.send(traceback.format_exc(), reference=message)


if __name__ == '__main__':
    client = SnapshotBot(command_prefix='')
    client.run(os.environ['TOKEN'])
