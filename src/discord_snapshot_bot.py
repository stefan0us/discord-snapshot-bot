import asyncio
import io
import logging
import os
import re
import sys
import uuid

import discord
from discord.ext.commands import Bot

from utils.playwright_helper import SnapshotTaskBase

logging.basicConfig(format="%(asctime)s %(message)s",
                    stream=sys.stdout, level=logging.INFO)


class CustomizedSnapshotTask(SnapshotTaskBase):

    async def pre_process_page(self, page):
        if re.search(r'(zhuanlan.|)zhihu.com/(people|answer|)', page.url) is not None:
            try:
                await page.click('//html/body/div[4]/div/div/div/div[2]/button')
            except Exception:
                self.logger.warning(
                    'failed to pre-process page.', exc_info=True)


class SnapshotBot(Bot):

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.url_patten = re.compile(r'(?P<url>https?://[^\s]+)')
        self.snapshot_task = CustomizedSnapshotTask()
        asyncio.get_event_loop().create_task(self.snapshot_task.get_task())
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        self.logger.info(f'discord server connected. [{self.user.name=}]')

    async def on_message(self, message):
        if message.author == self.user:
            return
        url_result = self.url_patten.search(message.content)
        if url_result is not None:
            snapshot_id = uuid.uuid4()
            await message.channel.send(file=discord.File(
                fp=io.BytesIO(await self.snapshot_task.snapshot(url_result['url'])),
                filename=f"{snapshot_id}.jpeg"),
                reference=message)


if __name__ == '__main__':
    client = SnapshotBot(command_prefix='')
    client.run(os.environ['TOKEN'])
