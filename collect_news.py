"""
Web3ニュース収集スクリプト

監視対象の企業ごとに Google News RSS を検索し、
Web3関連ニュースをMarkdown形式でまとめて出力する。

設定は config.json で管理する:
  - companies            : 監視対象の企業名リスト
  - web3_keywords        : 検索に使うWeb3関連キーワード
  - articles_per_company : 企業ごとの最大取得件数
  - output_file          : 最新結果の出力先ファイルパス
  - archive_dir          : 日付別アーカイブの保存ディレクトリ
"""

import html
import json
import re
import shutil
import feedparser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode


# ── 設定読み込み ──────────────────────────────────────────

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

COMPANIES: list[str] = config["companies"]
WEB3_KEYWORDS: list[str] = config["web3_keywords"]
ARTICLES_PER_COMPANY: int = config["articles_per_company"]
LATEST_DIR: str = config["latest_dir"]
ARCHIVE_DIR: str = config["archive_dir"]


# ── ユーティリティ ────────────────────────────────────────

def strip_html(text: str) -> str:
    """HTMLタグとHTMLエンティティ（&nbsp; 等）を除去してプレーンテキストに変換する。"""
    text = re.sub(r"<[^>]+>", "", text)       # タグ除去
    return html.unescape(text).strip()         # エンティティ変換 + 前後の空白除去


# ── RSSフェッチ ───────────────────────────────────────────

def build_url(company: str) -> str:
    """
    企業名とWeb3キーワードを組み合わせた Google News RSS の検索URLを生成する。

    クエリ例: 三菱UFJ銀行 (web3 OR ブロックチェーン OR 暗号資産 OR ...)
    """
    keyword_query = " OR ".join(WEB3_KEYWORDS)
    query = f"{company} ({keyword_query})"
    params = urlencode({"q": query, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
    return f"https://news.google.com/rss/search?{params}"


def fetch_news(company: str) -> list[dict]:
    """
    指定した企業のWeb3関連ニュースをGoogle News RSSから取得する。

    - feedparser でRSSを解析
    - タイトル・リンク・公開日・概要を抽出
    - 上位 ARTICLES_PER_COMPANY 件に絞る
    - URLはGoogle経由のリダイレクトURL（クリックすれば記事に飛べる）
    """
    url = build_url(company)
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:ARTICLES_PER_COMPANY]:
        articles.append({
            "title": strip_html(entry.get("title", "")),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": strip_html(entry.get("summary", "")),
        })
    return articles


def collect_all_news() -> dict[str, list[dict]]:
    """全企業のニュースを順番に取得して返す。"""
    result = {}
    for company in COMPANIES:
        print(f"取得中: {company}")
        articles = fetch_news(company)
        print(f"  {len(articles)} 件取得")
        result[company] = articles
    return result


# ── Markdown出力 ──────────────────────────────────────────

def save_to_markdown(news_by_company: dict[str, list[dict]], output_path: str) -> None:
    """
    企業ごとのニュースリストをMarkdownファイルに書き出す。

    出力形式:
      # Web3ニュース日次ダイジェスト
      ## 企業名（N件）
      ### [記事タイトル](URL)
      **公開日**: ...
      概要テキスト
    """
    total = sum(len(articles) for articles in news_by_company.values())

    # ヘッダー
    lines = [
        "# Web3ニュース日次ダイジェスト",
        "",
        f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"合計: {total} 件",
        "",
        "---",
        "",
    ]

    # 企業ごとのセクション
    for company, articles in news_by_company.items():
        lines.append(f"## {company}（{len(articles)} 件）")
        lines.append("")

        if not articles:
            lines.append("該当ニュースなし")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        for article in articles:
            lines.append(f"### [{article['title']}]({article['link']})")
            if article["published"]:
                lines.append(f"**公開日**: {article['published']}")
            if article["summary"]:
                lines.append("")
                lines.append(article["summary"])
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n合計 {total} 件を {output_path} に保存しました")


# ── HTML出力 ──────────────────────────────────────────────

def save_to_html(news_by_company: dict[str, list[dict]], output_path: str) -> None:
    """企業ごとのニュースリストをHTMLファイルに書き出す。"""
    total = sum(len(articles) for articles in news_by_company.values())
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 企業ごとのセクションHTMLを生成
    sections = []
    for company, articles in news_by_company.items():
        if not articles:
            article_html = '<p class="no-news">該当ニュースなし</p>'
        else:
            items = []
            for article in articles:
                title = html.escape(article["title"])
                link = html.escape(article["link"])
                published = html.escape(article["published"]) if article["published"] else ""
                summary = html.escape(article["summary"]) if article["summary"] else ""

                published_html = f'<div class="published">公開日: {published}</div>' if published else ""
                summary_html = f'<p class="summary">{summary}</p>' if summary else ""
                items.append(
                    f'<li class="article">'
                    f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>'
                    f'{published_html}'
                    f'{summary_html}'
                    f'</li>'
                )
            article_html = f'<ul class="article-list">{"".join(items)}</ul>'

        sections.append(
            f'<section class="company">'
            f'<h2>{html.escape(company)}<span class="count">{len(articles)}件</span></h2>'
            f'{article_html}'
            f'</section>'
        )

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Web3ニュース日次ダイジェスト</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: "Hiragino Sans", "Noto Sans JP", sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }}
    header {{ background: #1a1a2e; color: #fff; padding: 24px 32px; }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; }}
    header .meta {{ margin-top: 6px; font-size: 0.85rem; opacity: 0.7; }}
    main {{ max-width: 960px; margin: 32px auto; padding: 0 16px; }}
    .company {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); margin-bottom: 28px; padding: 24px 28px; }}
    .company h2 {{ font-size: 1.15rem; color: #1a1a2e; border-bottom: 2px solid #e0e4f0; padding-bottom: 10px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }}
    .count {{ font-size: 0.78rem; background: #e8ecf8; color: #4a5568; border-radius: 12px; padding: 2px 10px; font-weight: 500; }}
    .article-list {{ list-style: none; display: flex; flex-direction: column; gap: 14px; }}
    .article {{ border-left: 3px solid #4a6cf7; padding: 10px 14px; background: #f9faff; border-radius: 0 6px 6px 0; }}
    .article a {{ font-size: 0.97rem; font-weight: 600; color: #2d3a8c; text-decoration: none; }}
    .article a:hover {{ text-decoration: underline; }}
    .published {{ font-size: 0.78rem; color: #888; margin-top: 4px; }}
    .summary {{ font-size: 0.85rem; color: #555; margin-top: 6px; }}
    .no-news {{ color: #aaa; font-size: 0.9rem; }}
    footer {{ text-align: center; padding: 24px; font-size: 0.8rem; color: #aaa; }}
  </style>
</head>
<body>
  <header>
    <h1>Web3ニュース日次ダイジェスト</h1>
    <div class="meta">収集日時: {generated_at}　合計: {total}件</div>
  </header>
  <main>
    {"".join(sections)}
  </main>
  <footer>自動収集 by news_collect</footer>
</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML: {total} 件を {output_path} に保存しました")


# ── エントリーポイント ────────────────────────────────────

if __name__ == "__main__":
    news_by_company = collect_all_news()

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    year_str = now.strftime("%Y")
    month_str = now.strftime("%m")

    # latest/ を一旦クリアして今日の日付ファイルを書き込む
    # 例: latest/2026-04-17.md / latest/2026-04-17.html
    latest_dir = Path(LATEST_DIR)
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True)

    save_to_markdown(news_by_company, str(latest_dir / f"{date_str}.md"))
    save_to_html(news_by_company, str(latest_dir / f"{date_str}.html"))

    # アーカイブに年/月階層で保存
    # 例: archive/md/2026/04/2026-04-17.md / archive/html/2026/04/2026-04-17.html
    archive_base = Path(ARCHIVE_DIR)

    md_archive_path = archive_base / "md" / year_str / month_str / f"{date_str}.md"
    md_archive_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_markdown(news_by_company, str(md_archive_path))

    html_archive_path = archive_base / "html" / year_str / month_str / f"{date_str}.html"
    html_archive_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_html(news_by_company, str(html_archive_path))
