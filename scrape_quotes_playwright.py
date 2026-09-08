"""quotes.toscrape.com/js (JavaScript描画ページ) から名言・著者を収集する。

Markdownと screenshot を出力する。ブラウザは画面表示（headless=False）で起動する。
"""

import logging
import random
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
from urllib.error import URLError
from urllib.robotparser import RobotFileParser

from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://quotes.toscrape.com/"
TARGET_URL = "https://quotes.toscrape.com/js"
USER_AGENT = "quotes-scraper-practice/1.0 (+https://github.com/shirasaki-coder)"
MIN_WAIT_SEC = 1.0
MAX_WAIT_SEC = 3.0
PAGE_TIMEOUT_MS = 15000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scrape_quotes.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def load_robot_parser(base_url: str) -> RobotFileParser:
    robots_url = urljoin(base_url, "robots.txt")
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except URLError as e:
        logger.error("robots.txtの取得に失敗しました: %s", e)
        sys.exit(1)
    return rp


def polite_wait() -> None:
    wait_sec = random.uniform(MIN_WAIT_SEC, MAX_WAIT_SEC)
    logger.info("次のリクエストまで %.2f 秒待機します", wait_sec)
    time.sleep(wait_sec)


def scrape_quotes(target_url: str) -> tuple[list[dict], str]:
    date_str = datetime.now().strftime("%Y%m%d")
    screenshot_path = f"quotes_{date_str}.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(target_url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")
            page.wait_for_selector(".quote", timeout=PAGE_TIMEOUT_MS)

            quotes = []
            for quote_el in page.query_selector_all(".quote"):
                text_el = quote_el.query_selector(".text")
                author_el = quote_el.query_selector(".author")
                if text_el is None or author_el is None:
                    continue
                quotes.append({
                    "text": text_el.inner_text().strip(),
                    "author": author_el.inner_text().strip(),
                })

            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
            return quotes, screenshot_path
    except (PlaywrightError, PlaywrightTimeoutError) as e:
        logger.error("接続エラーが発生しました (%s): %s", target_url, e)
        sys.exit(1)


def save_as_markdown(quotes: list[dict], screenshot_path: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"quotes_{date_str}.md"

    lines = [
        "# quotes.toscrape.com (JS) 名言一覧",
        "",
        f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"収集元: {TARGET_URL}",
        f"件数: {len(quotes)}",
        "",
        "| No | 名言 | 著者 |",
        "| --- | --- | --- |",
    ]
    for i, quote in enumerate(quotes, start=1):
        text = quote["text"].replace("|", "\\|")
        author = quote["author"].replace("|", "\\|")
        lines.append(f"| {i} | {text} | {author} |")

    lines += ["", f"![screenshot]({screenshot_path})"]

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return filename


def main() -> None:
    rp = load_robot_parser(BASE_URL)
    if not rp.can_fetch(USER_AGENT, TARGET_URL):
        logger.warning("robots.txtにより %s へのアクセスは禁止されています。処理を中断します。", TARGET_URL)
        return

    polite_wait()
    quotes, screenshot_path = scrape_quotes(TARGET_URL)

    if not quotes:
        logger.warning("名言が1件も取得できませんでした")
        return

    md_filename = save_as_markdown(quotes, screenshot_path)
    logger.info(
        "完了: %d 件の名言を %s に、スクリーンショットを %s に保存しました",
        len(quotes), md_filename, screenshot_path,
    )


if __name__ == "__main__":
    main()
