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
import platform
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


# ── PNG出力 ───────────────────────────────────────────────

def _find_japanese_font() -> str | None:
    """日本語対応フォントのパスを返す。見つからない場合はNone。"""
    candidates = []
    if platform.system() == "Linux":
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    elif platform.system() == "Darwin":
        candidates = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc",
        ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def save_to_png(news_by_company: dict[str, list[dict]], output_path: str) -> None:
    """ニュースを縦長PNG画像として出力する。"""
    from PIL import Image, ImageDraw, ImageFont

    # ── 定数 ─────────────────────────────────────────────
    WIDTH       = 1200
    OUTER_PAD   = 40
    CARD_PAD    = 24
    ART_PAD_L   = 14    # アクセントバー後のテキスト左余白
    ACCENT_W    = 4     # アクセントバー幅
    HEADER_H    = 110
    HEADER_GAP  = 32
    CARD_GAP    = 20
    CARD_SHD    = 4     # シャドウオフセット
    FOOTER_H    = 50
    LINE_GAP    = 2     # 行間
    ART_TOP     = 10    # 記事内上マージン
    ART_BOTTOM  = 10    # 記事内下マージン

    # カラー
    C_BG          = (245, 247, 250)
    C_HEADER_BG   = (26,  26,  46)
    C_HEADER_TEXT = (255, 255, 255)
    C_HEADER_META = (160, 160, 190)
    C_CARD_BG     = (255, 255, 255)
    C_CARD_SHD    = (210, 215, 230)
    C_COMPANY     = (26,  26,  46)
    C_DIVIDER     = (224, 228, 240)
    C_ACCENT      = (74,  108, 247)
    C_TITLE       = (45,  58,  140)
    C_DATE        = (136, 136, 136)
    C_SUMMARY     = (85,  85,  85)
    C_NO_NEWS     = (170, 170, 170)
    C_FOOTER      = (170, 170, 170)
    C_COUNT_BG    = (232, 236, 248)
    C_COUNT_TEXT  = (74,  85,  104)

    # ── フォント ──────────────────────────────────────────
    font_path = _find_japanese_font()

    def mf(size: int) -> ImageFont.FreeTypeFont:
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    f_h1      = mf(30)
    f_meta    = mf(14)
    f_company = mf(20)
    f_count   = mf(13)
    f_art_ttl = mf(15)
    f_art_dat = mf(12)
    f_art_bod = mf(13)
    f_no_news = mf(13)
    f_footer  = mf(12)

    # ── ヘルパー ──────────────────────────────────────────
    def th(d: "ImageDraw.ImageDraw", font, sample: str = "テA") -> int:
        """テキスト行高さ。"""
        b = d.textbbox((0, 0), sample, font=font)
        return b[3] - b[1]

    def tw(d: "ImageDraw.ImageDraw", text: str, font) -> int:
        """テキスト幅。"""
        b = d.textbbox((0, 0), text, font=font)
        return b[2] - b[0]

    def wrap(d: "ImageDraw.ImageDraw", text: str, font, max_w: int) -> list[str]:
        """1文字単位で折り返す（日本語対応）。"""
        lines, cur = [], ""
        for ch in text:
            if tw(d, cur + ch, font) <= max_w:
                cur += ch
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        return lines or [""]

    # ── 高さ計算 ──────────────────────────────────────────
    content_w    = WIDTH - OUTER_PAD * 2
    card_inner_w = content_w - CARD_PAD * 2
    text_w       = card_inner_w - ACCENT_W - ART_PAD_L - 8

    dummy = Image.new("RGB", (WIDTH, 1))
    d     = ImageDraw.Draw(dummy)

    def article_h(d, article: dict) -> int:
        h = ART_TOP
        h += len(wrap(d, article["title"], f_art_ttl, text_w)) * (th(d, f_art_ttl) + LINE_GAP)
        if article["published"]:
            h += 4 + th(d, f_art_dat)
        if article["summary"]:
            h += 6 + len(wrap(d, article["summary"], f_art_bod, text_w)) * (th(d, f_art_bod) + LINE_GAP)
        h += ART_BOTTOM
        return h

    def card_h(d, articles: list[dict]) -> int:
        h = CARD_PAD + th(d, f_company) + 12 + 1 + 14
        if not articles:
            h += th(d, f_no_news)
        else:
            for i, art in enumerate(articles):
                h += article_h(d, art)
                if i < len(articles) - 1:
                    h += 1  # 記事間区切り線
        h += CARD_PAD
        return h

    total        = sum(len(v) for v in news_by_company.values())
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    card_heights = {company: card_h(d, articles) for company, articles in news_by_company.items()}
    total_h = HEADER_H + HEADER_GAP
    for ch in card_heights.values():
        total_h += ch + CARD_SHD + CARD_GAP
    total_h += FOOTER_H

    # ── 描画 ─────────────────────────────────────────────
    img  = Image.new("RGB", (WIDTH, total_h), C_BG)
    draw = ImageDraw.Draw(img)

    # ヘッダー
    draw.rectangle([0, 0, WIDTH, HEADER_H], fill=C_HEADER_BG)
    draw.text((OUTER_PAD, 28), "Web3ニュース日次ダイジェスト", font=f_h1, fill=C_HEADER_TEXT)
    draw.text(
        (OUTER_PAD, 28 + th(draw, f_h1) + 12),
        f"収集日時: {generated_at}　合計: {total}件",
        font=f_meta, fill=C_HEADER_META,
    )

    y = HEADER_H + HEADER_GAP

    for company, articles in news_by_company.items():
        ch = card_heights[company]
        x0, x1 = OUTER_PAD, OUTER_PAD + content_w

        # シャドウ + カード背景
        draw.rectangle([x0 + CARD_SHD, y + CARD_SHD, x1 + CARD_SHD, y + ch + CARD_SHD], fill=C_CARD_SHD)
        draw.rectangle([x0, y, x1, y + ch], fill=C_CARD_BG)

        cy = y + CARD_PAD

        # 企業名
        draw.text((x0 + CARD_PAD, cy), company, font=f_company, fill=C_COMPANY)
        # 件数バッジ
        count_text = f"{len(articles)}件"
        badge_x = x0 + CARD_PAD + tw(draw, company, f_company) + 12
        badge_y = cy + (th(draw, f_company) - th(draw, f_count)) // 2
        cw_px   = tw(draw, count_text, f_count)
        draw.rectangle(
            [badge_x - 6, badge_y - 3, badge_x + cw_px + 6, badge_y + th(draw, f_count) + 3],
            fill=C_COUNT_BG,
        )
        draw.text((badge_x, badge_y), count_text, font=f_count, fill=C_COUNT_TEXT)

        cy += th(draw, f_company) + 12
        draw.line([x0 + CARD_PAD, cy, x1 - CARD_PAD, cy], fill=C_DIVIDER, width=1)
        cy += 1 + 14

        if not articles:
            draw.text((x0 + CARD_PAD, cy), "該当ニュースなし", font=f_no_news, fill=C_NO_NEWS)
        else:
            for i, article in enumerate(articles):
                ax        = x0 + CARD_PAD
                tx        = ax + ACCENT_W + ART_PAD_L
                art_start = cy
                ay        = cy + ART_TOP

                for line in wrap(draw, article["title"], f_art_ttl, text_w):
                    draw.text((tx, ay), line, font=f_art_ttl, fill=C_TITLE)
                    ay += th(draw, f_art_ttl) + LINE_GAP

                if article["published"]:
                    ay += 4
                    draw.text((tx, ay), article["published"], font=f_art_dat, fill=C_DATE)
                    ay += th(draw, f_art_dat)

                if article["summary"]:
                    ay += 6
                    for line in wrap(draw, article["summary"], f_art_bod, text_w):
                        draw.text((tx, ay), line, font=f_art_bod, fill=C_SUMMARY)
                        ay += th(draw, f_art_bod) + LINE_GAP

                ay += ART_BOTTOM
                # アクセントバー
                draw.rectangle([ax, art_start + 4, ax + ACCENT_W, ay - 4], fill=C_ACCENT)
                cy = ay

                if i < len(articles) - 1:
                    draw.line([x0 + CARD_PAD, cy, x1 - CARD_PAD, cy], fill=C_DIVIDER, width=1)
                    cy += 1

        y += ch + CARD_SHD + CARD_GAP

    # フッター
    footer_text = "自動収集 by news_collect"
    fw = tw(draw, footer_text, f_footer)
    draw.text(((WIDTH - fw) // 2, y + 16), footer_text, font=f_footer, fill=C_FOOTER)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"PNG: {total} 件を {output_path} に保存しました")


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
    save_to_png(news_by_company, str(latest_dir / f"{date_str}.png"))

    # アーカイブに年/月階層で保存
    # 例: archive/md/2026/04/2026-04-17.md / archive/html/2026/04/2026-04-17.html
    #      archive/png/2026/04/2026-04-17.png
    archive_base = Path(ARCHIVE_DIR)

    md_archive_path = archive_base / "md" / year_str / month_str / f"{date_str}.md"
    md_archive_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_markdown(news_by_company, str(md_archive_path))

    html_archive_path = archive_base / "html" / year_str / month_str / f"{date_str}.html"
    html_archive_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_html(news_by_company, str(html_archive_path))

    png_archive_path = archive_base / "png" / year_str / month_str / f"{date_str}.png"
    png_archive_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_png(news_by_company, str(png_archive_path))
