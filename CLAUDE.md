# プロジェクト概要

金融系企業のWeb3関連ニュースを毎日自動収集し、Markdown形式で保存するスクリプト。
GitHub Actionsで毎朝9時（JST）に自動実行される。

# ファイル構成

```
collect_news.py      # メインスクリプト
config.json          # 設定ファイル（企業リスト・キーワード等）
requirements.txt     # 依存パッケージ（feedparser のみ）
news.md              # 最新の収集結果（毎日上書き）
archive/             # 日付別アーカイブ（YYYY-MM-DD.md）
.github/workflows/
  collect.yml        # GitHub Actions の日次実行ワークフロー
```

# 仕組み

1. `config.json` の `companies` × `web3_keywords` で Google News RSS を検索
2. 企業ごとに上位20件を取得（`feedparser` で解析）
3. `news.md`（最新）と `archive/YYYY-MM-DD.md`（アーカイブ）に出力
4. GitHub Actions が結果を自動コミット・push

## 検索クエリの例

```
三菱UFJ銀行 (web3 OR ブロックチェーン OR 暗号資産 OR ...)
```

## 注意点

- Google News のリンクURLはGoogleのリダイレクトURL（`news.google.com/rss/articles/...`）
  - Pythonからは実URLに解決できない（JavaScript/Cookie が必要）
  - クリックすれば記事に飛べるので実用上は問題なし
- GitHub Actions のpushには `permissions: contents: write` が必要（設定済み）

# ローカル実行

```bash
# 初回セットアップ
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 実行
.venv/bin/python collect_news.py
```

# 設定変更

`config.json` を編集する。スクリプト側の変更は不要。

| フィールド | 説明 |
|---|---|
| `companies` | 監視対象の企業名リスト |
| `web3_keywords` | 検索キーワード（OR検索） |
| `articles_per_company` | 企業ごとの最大取得件数 |
| `output_file` | 最新結果の出力先 |
| `archive_dir` | アーカイブの保存ディレクトリ |
