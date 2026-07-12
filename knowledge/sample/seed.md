# サンプル知識

これは Local Markdown RAG Chat 用の公開サンプル Markdown ファイルです。

このアプリは `knowledge/` 配下の Markdown ファイルを読み込み、検索しやすい単位に分割して embedding を作成します。
チャット時には、質問に関連する chunk を検索し、その内容を回答生成の文脈として利用します。

個人用メモ、会話ログ、非公開の知識データは Git に含めない運用です。
公開してよいサンプルだけを `knowledge/sample/` 配下に置きます。
