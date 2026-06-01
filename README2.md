# Local Markdown RAG Chat

Local Markdown RAG Chat は、ローカルの Markdown ファイルを知識源として使う、Python + FastAPI 製の最小構成 RAG チャットアプリです。

`knowledge/` 配下の Markdown を読み込み、chunk 化し、Ollama で embedding を作成して SQLite に保存します。ユーザーの入力に近い chunk を検索し、その検索結果を文脈としてローカル LLM に渡して回答を生成します。

このアプリは標準構成では OpenAI API などの外部 API を使いません。Ollama 上のローカルモデルを使用するため、外部 API 課金は発生しません。

## 主な機能

- FastAPI による HTTP API
- `knowledge/` 配下の Markdown 読み込み
- Markdown の chunk 化
- Ollama による embedding 生成
- SQLite への検索用データ保存
- Markdown chunk の類似検索
- RAG チャット API
- 2種類のペルソナ
- 最小構成の MCP サーバ
- `.env` による設定管理

## 既定モデル

既定では以下を使います。

- チャットモデル: `qwen3:8b`
- embedding モデル: `nomic-embed-text`
- Ollama API URL: `http://localhost:11434/api`

これらは `.env` で変更できます。

## 必要なもの

- Python
- Node.js
- Ollama
- `qwen3:8b`
- `nomic-embed-text`

Ollama のモデルを取得します。

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

Ollama が使えることを確認します。

```powershell
ollama list
```

## セットアップ

依存ライブラリをインストールします。

```powershell
pip install -r requirements.txt
```

`.env` を作成します。

```powershell
Copy-Item .env.example .env
```

`.env` の例:

```env
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BACKEND=ollama
```

## FastAPI サーバの起動

```powershell
uvicorn app.main:app --reload
```

API ドキュメントを開きます。

```text
http://127.0.0.1:8000/docs
```

8000 番ポートが使えない場合は、別のポートで起動します。

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

## Web UI の起動

Web UI は `web/` 配下にあります。FastAPI API サーバとは別プロセスで起動します。

初回のみ依存関係をインストールします。

```powershell
cd web
npm install
Copy-Item .env.example .env
```

`web/.env` の例:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Web UI を起動します。

```powershell
npm run dev
```

ブラウザで開きます。

```text
http://127.0.0.1:5173
```

利用時は、FastAPI サーバと Web UI の両方が起動している必要があります。

## 基本的な使い方

### 1. インデックスを再構築する

Markdown を追加・編集した後は、検索用インデックスを作り直します。

```text
POST /api/index/rebuild
```

レスポンス例:

```json
{
  "documents": 1,
  "chunks": 1,
  "embedding_backend": "ollama"
}
```

### 2. Markdown を検索する

```text
POST /api/search
```

リクエスト例:

```json
{
  "query": "このアプリの目的は？",
  "top_k": 3
}
```

### 3. チャットする

```text
POST /api/chat
```

リクエスト例:

```json
{
  "message": "このアプリの目的を説明して",
  "persona": "rational_advisor",
  "top_k": 3
}
```

## ペルソナ

標準で2つのペルソナを用意しています。

- `user_clone`: ユーザーの思考様式を反映することを目的にしたペルソナ
- `rational_advisor`: 批評的かつ構造化された助言を行うペルソナ

ペルソナ一覧は以下で取得できます。

```text
GET /api/personas
```

## knowledge ディレクトリ

アプリは `knowledge/` 配下の `.md` ファイルを再帰的に読み込みます。

推奨構成:

```text
knowledge/
  conversations/
  notes/
  seek/
  sample/
```

`conversations/`、`notes/`、`seek/` はローカルの個人用データ置き場です。公開リポジトリでは Git 管理に含めない想定です。

`sample/` は公開用のサンプル Markdown 置き場です。Git には `knowledge/sample/*.md` だけを含めます。

Markdown を追加・編集した後は、以下を実行してください。

```text
POST /api/index/rebuild
```

## MCP サーバ

MCP サーバとして起動できます。

```powershell
python -m app.mcp.server
```

提供 tool:

- `search_knowledge(query, top_k=4)`
- `get_persona_context(persona)`
- `save_note(title, content)`
- `list_notes(limit=50)`

MCP 対応クライアントから、このアプリをローカル Markdown 検索ツールとして利用できます。

## トラブルシューティング

### Ollama に接続できない

API が `503` を返す場合、Ollama が起動していない、URL が違う、または必要なモデルが取得されていない可能性があります。

確認:

```powershell
ollama list
```

必要に応じてモデルを取得します。

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 8000 番ポートが使えない

別ポートで起動します。

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### `__pycache__` が作られる

`__pycache__/` や `.pyc` は Python が自動生成するキャッシュです。Git 管理には含めず、削除しても問題ありません。

## プロジェクト構成

```text
app/
  main.py              FastAPI の入口
  config.py            アプリ設定
  ollama_client.py     Ollama API クライアント
  chat/                チャット API とペルソナ
  rag/                 Markdown 読み込み、chunk 化、embedding、検索
  db/                  SQLite 関連
  mcp/                 MCP サーバと tool
knowledge/             検索対象の Markdown
requirements.txt       Python 依存関係
.env.example           設定例
web/                   React + Vite + TypeScript の Web UI
```
