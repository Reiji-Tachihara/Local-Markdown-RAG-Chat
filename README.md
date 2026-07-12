# Local Markdown RAG Chat

ローカルの Markdown ファイルを知識ベースとして使う、FastAPI + React 製の RAG チャットアプリです。
Ollama 上のローカル LLM を利用し、標準設定では外部 API を使いません。検索対象の Markdown、SQLite データベース、会話履歴、個人メモはローカルに保持します。

## 主な機能

- `knowledge/` 配下の Markdown を読み込み、検索用 chunk として保存
- Ollama embedding による Markdown chunk の類似検索
- 検索結果を文脈として使う RAG チャット
- 回答に使われた参照元 chunk の表示
- ペルソナ切り替え
- SQLite への会話履歴保存
- MCP tool からの知識検索、ペルソナ取得、ノート保存、ノート一覧取得

## 技術スタック

```text
Backend
  Python
  FastAPI
  SQLite
  Ollama

Frontend
  React
  TypeScript
  Vite

Local AI
  qwen3:8b
  
```

## アーキテクチャ

```text
React / Vite frontend
  -> FastAPI API
      -> Chat service
      -> RAG retriever
          -> Markdown loader
          -> Chunker
          -> Embedder
          -> SQLite vector store
      -> Ollama API
      -> SQLite repositories
```

## プロジェクト構成

```text
app/                         FastAPI, RAG, DB, Ollama, MCP
  chat/                      チャットAPIとRAG応答サービス
  db/                        SQLite接続、schema、repository
  mcp/                       MCP serverとtool実装
  rag/                       Markdown loader、chunker、embedder、retriever
frontend/                    React + Vite + TypeScript UI
  src/api/                   FastAPI client
  src/components/            UI components
  src/hooks/                 React hooks
  src/types.ts               API/UI共通型
personas/                    ペルソナ定義 Markdown
knowledge/sample/            公開用サンプル Markdown
scripts/                     セットアップ・起動・公開前チェック用スクリプト
requirements.txt             Python dependencies
.env.example                 Backend environment example
frontend/.env.example        Frontend environment example
```

ローカル専用の `knowledge/` 本体、`data/`、`.env`、ビルド成果物は Git に含めない前提です。

## セットアップと起動

### 初回セットアップ

PowerShell でプロジェクトルートへ移動し、初回だけ以下を実行します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\setup_app.ps1
```

このスクリプトは `.env` 作成、Python 依存関係、frontend 依存関係、Ollama モデル取得をまとめて実行します。

### 普段の起動

Ollama アプリが起動している状態で、以下を実行します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_app.ps1
```

このスクリプトは FastAPI と React/Vite をまとめて起動し、ブラウザでフロントエンドを開きます。
停止するときは、起動中の PowerShell で `Ctrl + C` を押します。

Frontend:

```text
http://127.0.0.1:5173
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## 環境変数

詳細な設定項目は [.env.example](.env.example) と [frontend/.env.example](frontend/.env.example) に記載しています。
README では、動作理解に必要な主要項目だけを示します。

```env
OLLAMA_BASE_URL=http://localhost:11434/api
ENFORCE_LOCAL_OLLAMA=true
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`ENFORCE_LOCAL_OLLAMA=true` の場合、Ollama URL は `localhost` / `127.0.0.1` / `::1` のみ許可します。
API キーやパスワードのような秘密情報は使わない前提です。

## API

```text
POST /api/index/rebuild   Markdown knowledge index を再構築
POST /api/search          Markdown chunk を類似検索
POST /api/chat            RAG チャット応答を生成
GET  /api/personas        ペルソナ一覧を取得
GET  /api/chat/history    会話履歴を取得
GET  /health              API ヘルスチェック
```

## ペルソナ

ペルソナは `personas/` 配下の Markdown で定義します。

```text
personas/user_clone.md
personas/rational_advisor.md
```

UI 上では以下の表示名を使います。

```text
user_clone        ユーザー
rational_advisor  相談相手
```

## knowledge

RAG 対象の Markdown は `knowledge/` 配下に置きます。
公開用サンプルのみ `knowledge/sample/` に配置し、個人用メモや会話ログは Git に含めない運用です。

Markdown を追加・編集したら、UI の `Index rebuild` または API の `POST /api/index/rebuild` でインデックスを再構築します。

## MCP tools

MCP サーバとして起動できます。

```powershell
python -m app.mcp.server
```

提供 tool:

```text
search_knowledge
get_persona_context
save_note
list_notes
```
