# Local Markdown RAG Chat

ローカルの Markdown ファイルを知識ベースとして使う、FastAPI + React 製の RAG チャットアプリです。
Ollama 上のローカル LLM を利用し、標準設定では外部 API を使いません。検索対象の Markdown、SQLite データベース、会話履歴、個人メモはローカルに保持します。

## 目的

転職活動用のポートフォリオとして、以下を示すために制作しています。

- FastAPI による API 設計
- React + TypeScript によるフロントエンド実装
- Markdown ingestion、chunking、embedding、類似検索を含む RAG パイプライン
- SQLite を使ったローカル永続化
- Ollama 連携とローカルファーストな安全設計
- MCP tool としての検索・メモ保存機能

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
  nomic-embed-text
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
scripts/                     起動・公開前チェック用スクリプト
requirements.txt             Python dependencies
.env.example                 Backend environment example
frontend/.env.example        Frontend environment example
```

ローカル専用の `knowledge/` 本体、`data/`、`.env`、ビルド成果物は Git に含めない前提です。

## セットアップ

### 1. Ollama モデルを取得

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 2. Backend

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_api.ps1
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

### 3. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

## 環境変数

Backend settings are defined in `.env`.

```env
OLLAMA_BASE_URL=http://localhost:11434/api
ENFORCE_LOCAL_OLLAMA=true
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BACKEND=ollama
HASH_EMBEDDING_DIMENSIONS=384
KNOWLEDGE_DIR=knowledge
DATA_DIR=data
DATABASE_PATH=data/app.db
CHUNK_SIZE=900
CHUNK_OVERLAP=120
RETRIEVAL_LIMIT=4
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend settings are defined in `frontend/.env`.

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`ENFORCE_LOCAL_OLLAMA=true` の場合、Ollama URL は `localhost` / `127.0.0.1` / `::1` のみ許可します。

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

## 公開前チェック

個人データやローカル生成物が Git 管理に入っていないか確認します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_public_safety.ps1
```

## 設計上のポイント

- 外部 API キーを使わず、Ollama と SQLite でローカル完結できる構成
- RAG pipeline を loader / chunker / embedder / retriever / vector store に分離
- DB 層を connection / schema / repository に分離
- フロントエンドを API client / hooks / components / types に分離
- 公開用サンプルと個人用 knowledge を Git 管理上で分離

## 今後の改善候補

- API response model を Pydantic で明示
- `chunker`、`HashEmbedder`、DB repository のテスト追加
- RAG 参照表示の検索スコア可視化
- 会話履歴の削除・クリア機能
- Docker Compose による起動手順の簡略化
