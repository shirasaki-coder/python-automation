"""books.toscrape.com から書籍タイトル・価格・在庫状況を収集し、Markdownに出力する。"""

import logging
import os
import random
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
from urllib.error import URLError
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "books-scraper-practice/1.0 (+https://github.com/shirasaki-coder)"
MIN_WAIT_SEC = float(os.environ.get("BOOKS_MIN_WAIT_SEC", "1.0"))
MAX_WAIT_SEC = float(os.environ.get("BOOKS_MAX_WAIT_SEC", "3.0"))
REQUEST_TIMEOUT = int(os.environ.get("BOOKS_REQUEST_TIMEOUT", "10"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scrape.log", encoding="utf-8"),
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


def fetch(session: requests.Session, url: str) -> requests.Response:
    try:
        response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        # サーバーがContent-TypeにcharsetをつけないためHTTP仕様上ISO-8859-1に
        # フォールバックしてしまう。実際のページはUTF-8で配信されているため明示する。
        response.encoding = "utf-8"
        return response
    except requests.exceptions.RequestException as e:
        logger.error("接続エラーが発生しました (%s): %s", url, e)
        sys.exit(1)


def parse_books(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"].strip()
        price = article.select_one(".price_color").get_text(strip=True)
        stock = article.select_one(".instock.availability").get_text(strip=True)
        books.append({"title": title, "price": price, "stock": stock})
    return books


def find_next_page(html: str, current_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link is None:
        return None
    return urljoin(current_url, next_link["href"])


def scrape_all_books(rp: RobotFileParser) -> list[dict]:
    books = []
    current_url = BASE_URL
    session = requests.Session()
    page_count = 0

    while current_url:
        if not rp.can_fetch(USER_AGENT, current_url):
            logger.warning("robots.txtにより %s へのアクセスは禁止されています。処理を中断します。", current_url)
            break

        page_count += 1
        logger.info("ページ %d を取得中: %s", page_count, current_url)
        response = fetch(session, current_url)
        html = response.text

        page_books = parse_books(html)
        books.extend(page_books)
        logger.info("ページ %d から %d 件の書籍情報を取得しました", page_count, len(page_books))

        next_url = find_next_page(html, current_url)
        current_url = next_url

        if current_url:
            wait_sec = random.uniform(MIN_WAIT_SEC, MAX_WAIT_SEC)
            logger.info("次のリクエストまで %.2f 秒待機します", wait_sec)
            time.sleep(wait_sec)

    return books


def save_as_markdown(books: list[dict]) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"books_{date_str}.md"

    lines = [
        "# books.toscrape.com 書籍一覧",
        "",
        f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"収集元: {BASE_URL}",
        f"件数: {len(books)}",
        "",
        "| No | タイトル | 価格 | 在庫状況 |",
        "| --- | --- | --- | --- |",
    ]
    for i, book in enumerate(books, start=1):
        title = book["title"].replace("|", "\\|")
        lines.append(f"| {i} | {title} | {book['price']} | {book['stock']} |")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return filename


def main() -> None:
    rp = load_robot_parser(BASE_URL)
    books = scrape_all_books(rp)

    if not books:
        logger.warning("書籍情報が1件も取得できませんでした")
        return

    filename = save_as_markdown(books)
    logger.info("完了: %d 件の書籍情報を %s に保存しました", len(books), filename)


if __name__ == "__main__":
    main()
