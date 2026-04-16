import html
import re
import feedparser
from datetime import datetime
from urllib.parse import urlencode


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


COMPANIES = [
    "三菱UFJ銀行",
    "SBI証券",
    "みずほ銀行",
    "野村證券",
    "三井住友銀行",
    "マネックス証券",
    "GMOフィナンシャルホールディングス",
    "bitFlyer",
]

WEB3_KEYWORDS = [
    "web3",
    "ブロックチェーン",
    "暗号資産",
    "ステーブルコイン",
    "トークン化",
    "セキュリティトークン",
    "クリプト",
    "NFT",
    "DeFi",
]


def build_url(company: str) -> str:
    keyword_query = " OR ".join(WEB3_KEYWORDS)
    query = f"{company} ({keyword_query})"
    params = urlencode({"q": query, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
    return f"https://news.google.com/rss/search?{params}"


def fetch_news(company: str) -> list[dict]:
    url = build_url(company)
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:20]:
        articles.append({
            "title": strip_html(entry.get("title", "")),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": strip_html(entry.get("summary", "")),
        })
    return articles


def collect_all_news() -> dict[str, list[dict]]:
    result = {}
    for company in COMPANIES:
        print(f"取得中: {company}")
        articles = fetch_news(company)
        print(f"  {len(articles)} 件取得")
        result[company] = articles
    return result


def save_to_markdown(news_by_company: dict[str, list[dict]], output_path: str) -> None:
    total = sum(len(articles) for articles in news_by_company.values())
    lines = [
        "# Web3ニュース日次ダイジェスト",
        "",
        f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"合計: {total} 件",
        "",
        "---",
        "",
    ]

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


if __name__ == "__main__":
    news_by_company = collect_all_news()
    save_to_markdown(news_by_company, "news.md")
