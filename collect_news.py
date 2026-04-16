import feedparser
import re
from datetime import datetime


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


RSS_FEEDS = {
    "Google アラート": "https://www.google.co.jp/alerts/feeds/13715549885112167831/3268479610179157607",
}


def fetch_news(feed_name: str, feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "source": feed_name,
            "title": strip_html(entry.get("title", "")),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": strip_html(entry.get("summary", "")),
        })
    return articles


def collect_all_news() -> list[dict]:
    all_articles = []
    for name, url in RSS_FEEDS.items():
        print(f"取得中: {name}")
        articles = fetch_news(name, url)
        all_articles.extend(articles)
        print(f"  {len(articles)} 件取得")
    return all_articles


def save_to_markdown(articles: list[dict], output_path: str) -> None:
    lines = [
        f"# ニュース収集結果",
        f"",
        f"収集日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"件数: {len(articles)} 件",
        f"",
        "---",
        "",
    ]
    for article in articles:
        lines.append(f"## [{article['title']}]({article['link']})")
        if article["published"]:
            lines.append(f"**公開日**: {article['published']}")
        if article["summary"]:
            lines.append(f"")
            lines.append(article["summary"])
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n{len(articles)} 件を {output_path} に保存しました")


if __name__ == "__main__":
    articles = collect_all_news()
    save_to_markdown(articles, "news.md")
