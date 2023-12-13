import asyncio
import logging
import sys
from typing import Coroutine

from playwright.async_api import async_playwright

from utils.object_pool import AsyncObjectPool
from utils.page_processer import page_preprocess_list


class SnapshotHandler:

    def __init__(self, pool_size=3, loading_timeout=3e5):
        self.page_pool: AsyncObjectPool = None
        self.pool_size = pool_size
        self.loading_timeout = loading_timeout
        self.ready = False
        self.logger = logging.getLogger(__name__)

    def get_task(self) -> Coroutine:
        return self._playwright_browser_task()

    async def _playwright_browser_task(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0')
            await context.add_init_script(path='stealth.min.js')
            self.page_pool = AsyncObjectPool(create_func=context.new_page, max_size=self.pool_size)
            self.ready = True
            await asyncio.sleep(sys.float_info.max)

    async def snapshot(self, url, format='jpeg') -> dict:
        self.logger.info(f"request to take snapshot. [{url=}]")
        await self._assert_ready()
        async with self.page_pool.acquire() as page:
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
