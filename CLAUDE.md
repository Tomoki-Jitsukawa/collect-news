# このファイルについて

このファイルはClaude Codeが会話開始時に自動で読み込むプロジェクトの引き継ぎ資料。
**コードやファイル構成に変更を加えたときは、必ずこのファイルも更新すること。**
更新対象の例：ファイルの追加・削除、仕組みの変更、注意点の追加、設定項目の変更。

---

# プロジェクト概要

金融系企業のWeb3関連ニュースを毎日自動収集し、MarkdownおよびHTML形式で保存するスクリプト。
GitHub Actionsで毎朝9時（JST）に自動実行される。

# ファイル構成

```
collect_news.py      # メインスクリプト
config.json          # 設定ファイル（企業リスト・キーワード等）
requirements.txt     # 依存パッケージ（feedparser・Pillow）
latest/               # 最新ファイル（毎日クリア→日付ファイルを書き込み）
  YYYY-MM-DD.md
  YYYY-MM-DD.html
  YYYY-MM-DD.png
archive/
  md/               # Markdownアーカイブ
    YYYY/
      MM/
        YYYY-MM-DD.md
  html/             # HTMLアーカイブ
    YYYY/
      MM/
        YYYY-MM-DD.html
  png/              # PNG画像アーカイブ
    YYYY/
      MM/
        YYYY-MM-DD.png
.github/workflows/
  collect.yml        # GitHub Actions の日次実行ワークフロー
```

# 仕組み

1. `config.json` の `companies` × `web3_keywords` で Google News RSS を検索
2. 企業ごとに上位20件を取得（`feedparser` で解析）
3. `latest/YYYY-MM-DD.md` / `.html` / `.png`（最新）と `archive/md|html|png/YYYY/MM/YYYY-MM-DD.*`（アーカイブ）に出力
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
| `latest_dir` | 最新ファイルの出力先（実行のたびにクリアされ、日付ファイルが生成される） |
| `archive_dir` | アーカイブのルートディレクトリ（配下に `md/YYYY/MM/` `html/YYYY/MM/` `png/YYYY/MM/` が自動生成される） |
