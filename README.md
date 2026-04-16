# collect-news

企業ごとのWeb3関連ニュースをGoogle News RSSから収集し、Markdown形式で出力するスクリプト。

## 機能

- `config.json` に登録した企業名 × Web3キーワードで Google News RSS を検索
- 企業ごとに最新ニュースを取得してセクション分けしたMarkdownを生成
- HTMLタグ・エンティティを除去してプレーンテキストで出力

## セットアップ

```bash
# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使い方

```bash
python collect_news.py
```

実行すると `news.md` が生成される。

## 設定

`config.json` を編集することで監視対象や検索条件を変更できる。

```json
{
  "companies": ["三菱UFJ銀行", "SBI証券", ...],
  "web3_keywords": ["web3", "ブロックチェーン", ...],
  "articles_per_company": 20,
  "output_file": "news.md"
}
```

| フィールド | 説明 |
|---|---|
| `companies` | 監視対象の企業名リスト |
| `web3_keywords` | 検索に使うキーワード（OR検索） |
| `articles_per_company` | 企業ごとの最大取得件数 |
| `output_file` | 出力先のファイルパス |

## 出力例

```
# Web3ニュース日次ダイジェスト

収集日時: 2026-04-17 00:20:00
合計: 160 件

---

## 三菱UFJ銀行（20 件）

### [記事タイトル](https://...)
**公開日**: Thu, 17 Apr 2026 ...

記事の概要テキスト

---
```
