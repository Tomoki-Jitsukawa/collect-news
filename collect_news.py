import feedparser
import json
from datetime import datetime


RSS_FEEDS = {
    "NHK": "https://www3.nhk.or.jp/rss/news/cat0.xml",
    "朝日新聞": "https://www.asahi.com/rss/asahi/newsheadlines.rdf",
    "Yahoo!ニュース": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
}


def fetch_news(feed_name: str, feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:10]:
        articles.append({
            "source": feed_name,
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", ""),
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


def save_to_json(articles: list[dict], output_path: str) -> None:
    data = {
        "collected_at": datetime.now().isoformat(),
        "total": len(articles),
        "articles": articles,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n{len(articles)} 件を {output_path} に保存しました")


if __name__ == "__main__":
    articles = collect_all_news()
    save_to_json(articles, "news.json")
