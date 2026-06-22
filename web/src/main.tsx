import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

// document.getElementById("root") は index.html の <div id="root"> を取得する。
// createRoot(...).render(...) は、その場所に React アプリを描画する関数呼び出し。
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    {/* App は web/src/App.tsx で宣言しているメイン画面コンポーネント。 */}
    <App />
  </React.StrictMode>
);
