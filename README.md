# python-automation

Webスクレイピングの練習用スクリプトを収録したプロジェクトです。BeautifulSoupで静的サイト（books.toscrape.com）を、Playwrightでブラウザ制御によりJavaScript描画サイト（quotes.toscrape.com/js）を収集します。

## 概要

- `scrape_books.py`: books.toscrape.com から書籍タイトル・価格・在庫状況を収集し、Markdownに出力します。
- `scrape_quotes_playwright.py`: quotes.toscrape.com/js（JS描画ページ）をPlaywrightで開き、名言・著者を収集してMarkdownとスクリーンショットに出力します。

いずれも `robots.txt` を確認して禁止パスへはアクセスせず、リクエスト間に1〜3秒のランダムな待機を挟みます。

## 必要な環境

- Python 3.14 系（開発時: 3.14.7）
- ライブラリ（[requirements.txt](requirements.txt)）
  - `requests`
  - `beautifulsoup4`
  - `playwright`（別途ブラウザバイナリのインストールが必要）

## セットアップ手順

```powershell
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化（PowerShell）
.venv\Scripts\Activate.ps1

# 依存ライブラリのインストール
pip install -r requirements.txt

# Playwright用ブラウザ（Chromium）のインストール
python -m playwright install chromium
```

## 実行方法

```powershell
# books.toscrape.com のスクレイピング（BeautifulSoup）
python scrape_books.py

# quotes.toscrape.com/js のスクレイピング（Playwright）
python scrape_quotes_playwright.py
```

### 出力ファイル

| スクリプト | 出力ファイル | 内容 |
| --- | --- | --- |
| `scrape_books.py` | `books_<実行日YYYYMMDD>.md` | 書籍一覧（タイトル・価格・在庫状況） |
| `scrape_books.py` | `scrape.log` | 実行ログ（エラー時はここに記録） |
| `scrape_quotes_playwright.py` | `quotes_<実行日YYYYMMDD>.md` | 名言一覧（名言・著者） |
| `scrape_quotes_playwright.py` | `quotes_<実行日YYYYMMDD>.png` | ページ全体のスクリーンショット |
| `scrape_quotes_playwright.py` | `scrape_quotes.log` | 実行ログ（エラー時はここに記録） |

## 設定できる項目（環境変数）

すべて未設定時はデフォルト値で動作します。PowerShellでは `$env:変数名 = "値"` で設定してください。

| 変数名 | 対象スクリプト | 説明 | デフォルト値 |
| --- | --- | --- | --- |
| `BOOKS_MIN_WAIT_SEC` | scrape_books.py | リクエスト間待機時間の下限（秒） | `1.0` |
| `BOOKS_MAX_WAIT_SEC` | scrape_books.py | リクエスト間待機時間の上限（秒） | `3.0` |
| `BOOKS_REQUEST_TIMEOUT` | scrape_books.py | HTTPリクエストのタイムアウト（秒） | `10` |
| `QUOTES_MIN_WAIT_SEC` | scrape_quotes_playwright.py | リクエスト間待機時間の下限（秒） | `1.0` |
| `QUOTES_MAX_WAIT_SEC` | scrape_quotes_playwright.py | リクエスト間待機時間の上限（秒） | `3.0` |
| `QUOTES_PAGE_TIMEOUT_MS` | scrape_quotes_playwright.py | ページ読み込み・要素待機のタイムアウト（ミリ秒） | `15000` |
| `QUOTES_HEADLESS` | scrape_quotes_playwright.py | `true`にするとブラウザを非表示（ヘッドレス）で起動 | `false`（画面表示） |

例（PowerShell）:

```powershell
$env:QUOTES_HEADLESS = "true"
$env:BOOKS_MIN_WAIT_SEC = "2.0"
python scrape_quotes_playwright.py
```

## よくあるエラーと対処法

| 症状 | 原因 | 対処法 |
| --- | --- | --- |
| `接続エラーが発生しました` のログを出力して終了する | 対象サイトに接続できない（ネットワーク不通、サイト側の障害、タイムアウト） | インターネット接続とサイトの稼働状況を確認し、再実行する。タイムアウトが頻発する場合は `BOOKS_REQUEST_TIMEOUT` / `QUOTES_PAGE_TIMEOUT_MS` を増やす |
| `robots.txtにより...アクセスは禁止されています` と表示されて処理が中断する | 対象サイトの `robots.txt` が該当パスへのアクセスを禁止している | 仕様通りの動作。対象サイトのポリシーに従い、そのパスへのアクセスは行わない |
| `robots.txtの取得に失敗しました` | `robots.txt` へのアクセス自体がネットワークエラーで失敗 | ネットワーク接続を確認して再実行する |
| コンソール上で日本語ログが文字化けする（例: `�y�[�W`） | Windowsのコンソールが既定でUTF-8以外のコードページになっている | ログの内容自体はUTF-8で正しく保存されている（`scrape.log` / `scrape_quotes.log`）。コンソール表示を直す場合は事前に `chcp 65001` を実行するか、`$env:PYTHONIOENCODING = "utf-8"` を設定する |
| `playwright._impl._errors.Error: Executable doesn't exist` 等でPlaywright実行時にブラウザが見つからない | Playwright本体はインストール済みだがブラウザバイナリが未取得 | `python -m playwright install chromium` を実行する |
| `ModuleNotFoundError: No module named 'bs4'` / `'playwright'` など | 仮想環境が有効化されていない、または依存関係が未インストール | `.venv\Scripts\Activate.ps1` で仮想環境を有効化してから `pip install -r requirements.txt` を実行する |
| Playwright実行時にブラウザ画面が表示されない・固まる | リモートデスクトップや画面のないサーバー環境で `QUOTES_HEADLESS=false`（既定）のまま実行している | 画面表示が不要な環境では `QUOTES_HEADLESS=true` を設定してヘッドレスで実行する |
