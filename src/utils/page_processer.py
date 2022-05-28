import re

from playwright.async_api import Page

page_preprocess_list = []


def preprocess(page_preprocess_func):
    page_preprocess_list.append(page_preprocess_func)
    return page_preprocess_func


@preprocess
async def remove_zhihu_login_window(page: Page):
    if re.search(r'(zhuanlan.|)zhihu.com/(people|answer|)', page.url):
        await page.keyboard.press('Escape')
