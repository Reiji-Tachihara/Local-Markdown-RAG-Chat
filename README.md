# Local Markdown RAG Chat

Local Markdown RAG Chat は、ローカルの Markdown ファイルを知識源として使う Python + FastAPI 製の RAG チャットアプリです。

Ollama 上のローカルモデルを使用し、標準構成では OpenAI API などの外部 API を使いません。検索対象の Markdown、SQLite データベース、個人用メモはローカルに保持する前提です。

## 主な機能

- FastAPI による API サーバ
- React + Vite + TypeScript による Web UI
- `knowledge/` 配下の Markdown 読み込み
- Markdown の chunk 化
- Ollama による embedding 生成
- SQLite への検索用データ保存
- Markdown chunk の類似検索
- RAG チャット API
- ペルソナ切り替え
- Markdown ファイルによるペルソナ定義
- SQLite へのチャット履歴保存
- RAG 参照元表示
- MCP サーバの最小実装

## 構成

```text
React Web UI
  ↓ fetch
FastAPI API Server
  ↓
RAG Retriever
  ↓
SQLite Vector Store
  ↓
Ollama API
```

## 既定モデル

- チャットモデル: `qwen3:8b`
- embedding モデル: `nomic-embed-text`
- Ollama API URL: `http://localhost:11434/api`

これらの値は `.env` で変更できます。
標準では `ENFORCE_LOCAL_OLLAMA=true` により、Ollama URL は `localhost` / `127.0.0.1` / `::1` のみ許可します。

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

## バックエンドのセットアップ

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

FastAPI サーバを起動します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_api.ps1
```

API ドキュメント:

```text
http://127.0.0.1:8000/docs
```

## Web UI のセットアップ

```powershell
cd web
npm install
Copy-Item .env.example .env
npm run dev
```

Web UI:

```text
http://127.0.0.1:5173
```

`web/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## ローカル起動スクリプト

開発用に PowerShell スクリプトを用意しています。FastAPI と Web UI は別々の PowerShell で起動します。

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_api.ps1
powershell.exe -ExecutionPolicy Bypass -File .\scripts\start_web.ps1
```

ダブルクリックで起動したい場合は、`.ps1` ではなく `.cmd` を使います。

```text
scripts/start_api.cmd
scripts/start_web.cmd
```

`start_api.ps1` は FastAPI を `127.0.0.1` に限定して起動します。
停止するときは、起動している PowerShell で `Ctrl + C` を押します。

## API

インデックス再構築:

```text
POST /api/index/rebuild
```

Markdown chunk 検索:

```text
POST /api/search
```

チャット:

```text
POST /api/chat
```

ペルソナ一覧:

```text
GET /api/personas
```

チャット履歴:

```text
GET /api/chat/history
```

## ペルソナ

内部IDは以下のままですが、Web UI では短い表示名を使います。

- `user_clone`: 表示名 `ユーザー`
- `rational_advisor`: 表示名 `相談相手`

ペルソナの内容は `personas/` 配下の Markdown で定義します。

## knowledge ディレクトリ

アプリは `knowledge/` 配下の Markdown ファイルを再帰的に読み込みます。

公開用サンプルは以下に置きます。

```text
knowledge/sample/
```

個人用メモ、会話ログ、ローカル知識データは Git に含めない想定です。このリポジトリでは `knowledge/sample/` 配下の公開用 Markdown だけを追跡する設定にしています。

push 前の確認用スクリプト:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_public_safety.ps1
```

## MCP サーバ

MCP サーバとして起動できます。

```powershell
python -m app.mcp.server
```

提供 tool:

- `search_knowledge`
- `get_persona_context`
- `save_note`
- `list_notes`

## プロジェクト構成

```text
app/                  FastAPI, RAG, DB, Ollama, MCP
web/                  React + Vite + TypeScript UI
personas/             ペルソナ Markdown
knowledge/sample/     公開用サンプル Markdown
scripts/              ローカル起動スクリプト
requirements.txt      Python 依存関係
.env.example          バックエンド設定例
```
