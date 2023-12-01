import asyncio
import logging
import sys
from typing import Coroutine

from playwright.async_api import async_playwright

from utils.object_pool import AsyncObjectPool
from utils.page_processer import page_preprocess_list


class SnapshotHandler:

    def __init__(self, pool_size=3, loading_timeout=3e5):
        self.page_pool = None
        self.pool_size = pool_size
        self.loading_timeout = loading_timeout
        self.ready = False
        self.logger = logging.getLogger(__name__)

    def get_task(self, close_checker) -> Coroutine:
        return self._playwright_browser_task(close_checker)

    async def _playwright_browser_task(self, close_checker):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            self.page_pool = await AsyncObjectPool.new_instance(browser.new_page, self.pool_size)
            self.ready = True
            while not close_checker():
                await asyncio.sleep(1)

    async def snapshot(self, url, format='jpeg') -> dict:
        self.logger.info(f"request to take snapshot. [{url=}]")
        await self._assert_ready()
        page = await self.page_pool.acquire()
        await self.load_page(page, url)
        for page_preprocessor in page_preprocess_list:
            await page_preprocessor(page)
        result = {'title': await page.title()}
        if format == 'jpeg':
            snapshot_bytes = await page.screenshot(full_page=True, type='jpeg')
        elif format == 'mhtml':
            client = await page.context.new_cdp_session(page)
            response = await client.send(method='Page.captureSnapshot', params={'format': 'mhtml'})
            snapshot_bytes = response['data'].encode()
        result['content'] = snapshot_bytes
        self.logger.info(f"snapshot saved. [{url=}, {result['title']=}]")
        await self.page_pool.release(page)
        return result

    async def _assert_ready(self):
        if self.ready:
            return
        cond = asyncio.Condition()
        async with cond:
            await cond.wait_for(lambda: self.ready)

    async def load_page(self, page, url):
        await page.goto(url, wait_until='domcontentloaded')
        scroll_height = await page.evaluate('document.body.scrollHeight')
        self.logger.info(f'find scroll height. [{scroll_height=}, {url=}]')
        for height in range(0, scroll_height, 100):
            self.logger.debug(
                f'trace current height. [{height=}, {scroll_height=}, {url=}]')
            await page.evaluate(f'() => window.scrollTo(0, {height})')
            await asyncio.sleep(0.1)
        await page.evaluate('() => window.scrollTo(0, 0)')
        try:
            await page.wait_for_load_state(state='networkidle', timeout=self.loading_timeout)
        except Exception:
            self.logger.exception('failed to load page.')
