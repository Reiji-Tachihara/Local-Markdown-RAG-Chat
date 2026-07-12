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
cd E:\pwork
powershell.exe -ExecutionPolicy Bypass -File .\scripts\setup_app.ps1
```

このスクリプトは `.env` 作成、Python 依存関係、frontend 依存関係、Ollama モデル取得をまとめて実行します。

### 普段の起動

以下を実行します。

```powershell
cd E:\pwork
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_app.ps1
```

このスクリプトは Ollama、FastAPI、React/Vite をまとめて起動し、ブラウザでフロントエンドを開きます。
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

## 画面上のボタン

### Index rebuild

`Index rebuild` は、`knowledge/` 配下の Markdown を読み直して RAG 検索用のインデックスを作り直すボタンです。

主に以下のタイミングで使います。

- `knowledge/` に Markdown を追加した
- 既存の Markdown を編集した
- Markdown を削除した
- MCP の `save_note` 以外の方法で知識ファイルを変更した

内部的には以下の処理を行います。

```text
1. knowledge/ 配下の .md ファイルを読み込む
2. Markdown を chunk に分割する
3. 各 chunk の embedding を Ollama で作る
4. SQLite に chunk と embedding を保存し直す
5. 削除済み Markdown 由来の古い chunk を DB から消す
```

呼び出している API:

```text
POST /api/index/rebuild
```

### Reload history

`Reload history` は、SQLite に保存されている過去のチャット履歴を読み直すボタンです。

主に以下のタイミングで使います。

- 画面を開いたまま別操作で履歴が増えた
- 表示中の会話履歴を保存済みデータで再読み込みしたい
- 最後の assistant 回答に紐づく RAG references を再表示したい

内部的には以下の処理を行います。

```text
1. FastAPI の /api/chat/history を呼ぶ
2. SQLite の chat_messages テーブルから履歴を取得する
3. 画面上の会話一覧を取得した履歴で更新する
4. 最後の assistant 回答に紐づく RAG references を右側に表示する
```

呼び出している API:

```text
GET /api/chat/history?limit=80
```

画面を開いた時にも履歴は自動で読み込まれるため、通常は必要な時だけ押す手動更新ボタンです。

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

長い質問で応答に時間がかかる場合は、`.env.example` を参考に以下の値を調整できます。

```env
OLLAMA_REQUEST_TIMEOUT=180
CHAT_MESSAGE_MAX_CHARS=12000
RAG_CONTEXT_MAX_CHARS=12000
```

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
