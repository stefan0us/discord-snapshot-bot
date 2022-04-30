import re

from utils.playwright_helper import SnapshotHandlerBase


class CustomizedSnapshotHandler(SnapshotHandlerBase):

    async def pre_process_page(self, page):
        if re.search(r'(zhuanlan.|)zhihu.com/(people|answer|)', page.url):
            try:
                await page.click('//html/body/div[4]/div/div/div/div[2]/button')
            except Exception:
                self.logger.warning(
                    'failed to pre-process page.', exc_info=True)
