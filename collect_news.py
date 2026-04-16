"""
Web3ニュース収集スクリプト

監視対象の企業ごとに Google News RSS を検索し、
Web3関連ニュースをMarkdown形式でまとめて出力する。

設定は config.json で管理する:
  - companies       : 監視対象の企業名リスト
  - web3_keywords   : 検索に使うWeb3関連キーワード
  - articles_per_company : 企業ごとの最大取得件数
  - output_file     : 出力先ファイルパス
"""

import html
import json
import re
import feedparser
from datetime import datetime
from urllib.parse import urlencode


# ── 設定読み込み ──────────────────────────────────────────

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

COMPANIES: list[str] = config["companies"]
WEB3_KEYWORDS: list[str] = config["web3_keywords"]
ARTICLES_PER_COMPANY: int = config["articles_per_company"]
OUTPUT_FILE: str = config["output_file"]


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


# ── エントリーポイント ────────────────────────────────────

if __name__ == "__main__":
    news_by_company = collect_all_news()
    save_to_markdown(news_by_company, OUTPUT_FILE)
