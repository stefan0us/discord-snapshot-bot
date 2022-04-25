import asyncio
import logging
import sys
from typing import Coroutine

from playwright.async_api import async_playwright

from utils.object_pool import AsyncObjectFactory, AsyncObjectPool


class SnapshotTaskBase:

    def __init__(self, pool_size=3, loading_timeout=3e5):
        self.page_pool = None
        self.pool_size = pool_size
        self.loading_timeout = loading_timeout
        self.ready = False
        self.logger = logging.getLogger(__name__)

    def get_task(self) -> Coroutine:
        return self._playwright_browser_forever()

    async def _playwright_browser_forever(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            class PageFactory(AsyncObjectFactory):
                async def create(self):
                    return await browser.new_page()
            self.page_pool = await AsyncObjectPool.new_instance(PageFactory(), self.pool_size)
            self.ready = True
            await asyncio.sleep(sys.float_info.max)

    async def snapshot(self, url, format='jpeg') -> dict:
        self.logger.info(f"request to take snapshot. [{url=}]")
        await self._assert_ready()
        page_instance = await self.page_pool.acquire()
        await self._load_page(page_instance, url)
        await self.pre_process_page(page_instance)
        snapshot_result = {'title': await page_instance.title()}
        if format == 'jpeg':
            snapshot_result['jpeg'] = await page_instance.screenshot(full_page=True, type='jpeg')
        elif format == 'mhtml':
            client = await page_instance.context.new_cdp_session(page_instance)
            response = await client.send(method='Page.captureSnapshot', params={'format': 'mhtml'})
            snapshot_result['mhtml'] = response['data'].encode()
        self.logger.info(f"snapshot saved. [{url=}]")
        await self.page_pool.release(page_instance)
        return snapshot_result

    async def _assert_ready(self):
        if self.ready:
            return
        cond = asyncio.Condition()
        async with cond:
            await cond.wait_for(lambda: self.ready)

    async def _load_page(self, page, url):
        await page.goto(url, wait_until='domcontentloaded')
        try:
            await page.wait_for_load_state(state='networkidle', timeout=self.loading_timeout)
        except Exception:
            self.logger.warning('failed to load page.', exc_info=True)

    async def pre_process_page(self, page):
        pass
