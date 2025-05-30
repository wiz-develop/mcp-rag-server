#!/usr/bin/env python
"""
HTTP MCP RAG Server

FastMCPを使用したStreamable HTTP対応のModel Context Protocol (MCP)に準拠したRAG機能を持つPythonサーバー
"""

import sys
import os
import argparse
import importlib
import logging
from dotenv import load_dotenv

from .http_mcp_server import HTTPMCPServer


def main():
    """
    メイン関数

    コマンドライン引数を解析し、HTTP MCPサーバーを起動します。
    """
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="HTTP MCP RAG Server - FastMCPを使用したStreamable HTTP対応のModel Context Protocol (MCP)に準拠したRAG機能を持つPythonサーバー"
    )
    parser.add_argument("--name", default="mcp-rag-server", help="サーバー名")
    parser.add_argument("--version", default="0.1.0", help="サーバーバージョン")
    parser.add_argument("--host", default="127.0.0.1", help="サーバーのホスト（デフォルト: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8000, help="サーバーのポート（デフォルト: 8000）")
    parser.add_argument("--path", default="/mcp", help="MCPエンドポイントのパス（デフォルト: /mcp）")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="ログレベル")
    args = parser.parse_args()

    # 環境変数の読み込み
    load_dotenv()

    # ディレクトリの作成
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.environ.get("SOURCE_DIR", "data/source"), exist_ok=True)
    os.makedirs(os.environ.get("PROCESSED_DIR", "data/processed"), exist_ok=True)

    # ロギングの設定
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(os.path.join("logs", "http_mcp_rag_server.log"), encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("http_main")

    try:
        # HTTP MCPサーバーの作成
        server = HTTPMCPServer(name=args.name, version=args.version)

        logger.info(f"HTTP MCPサーバー '{args.name}' を起動しています...")
        logger.info(f"ホスト: {args.host}")
        logger.info(f"ポート: {args.port}")
        logger.info(f"パス: {args.path}")

        # HTTP MCPサーバーの起動
        server.run(host=args.host, port=args.port, path=args.path)

    except KeyboardInterrupt:
        logger.info("サーバーを終了します。")
        sys.exit(0)

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()