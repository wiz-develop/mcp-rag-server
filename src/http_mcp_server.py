#!/usr/bin/env python
"""
HTTP MCPサーバーモジュール

FastMCPを使用してStreamable HTTP MCPサーバーを提供します。
"""

import logging
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP
from .rag_service import RAGService
from .rag_tools import create_rag_service_from_env, search_handler, get_document_count_handler
from .example_tool import get_system_info, get_current_time, echo


class HTTPMCPServer:
    """
    FastMCPを使用したHTTP MCPサーバークラス

    Streamable HTTP通信を使用してクライアントからのリクエストを処理します。
    """

    def __init__(self, name: str = "mcp-rag-server", version: str = "0.1.0"):
        """
        HTTPMCPServerのコンストラクタ

        Args:
            name: サーバー名
            version: サーバーバージョン
        """
        self.name = name
        self.version = version

        # FastMCPインスタンスの作成
        self.mcp = FastMCP(
            name=self.name,
            stateless_http=True,  # ステートレス通信を有効化
            json_response=True,   # Server-Sent Events (SSE)を無効化
            log_level="INFO"      # ログレベル設定
        )

        # ロガーの設定
        self.logger = logging.getLogger("http_mcp_server")
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラの設定
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "http_mcp_server.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # フォーマッタの設定
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # ハンドラの追加
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

        # ツールを登録
        self._register_tools()

    def _register_tools(self):
        """
        ツールをFastMCPに登録します
        """
        # RAGサービスの初期化
        try:
            self.logger.info("RAGサービスを初期化しています...")
            self.rag_service = create_rag_service_from_env()
            self.logger.info("RAGサービスの初期化が完了しました")
        except Exception as e:
            self.logger.error(f"RAGサービスの初期化に失敗しました: {str(e)}")
            raise

        # サンプルツールの登録
        self._register_example_tools()

        # RAGツールの登録
        if self.rag_service:
            self._register_rag_tools()
        else:
            self.logger.warning("RAGサービスが初期化されていないため、RAGツールをスキップします")


    def _register_example_tools(self):
        """
        サンプルツールを登録します
        """
        @self.mcp.tool('get_system_info')
        def get_system_info_wrapper() -> dict:
            """システム情報を取得します"""
            # example_tool.pyのget_system_info関数を使用
            params = {}
            return get_system_info(params)

        @self.mcp.tool('get_current_time')
        def get_current_time_wrapper(format: str = "%Y-%m-%d %H:%M:%S") -> dict:
            """
            現在の日時を取得します

            Args:
                format: 日時のフォーマット（例: '%Y-%m-%d %H:%M:%S'）
            """
            # example_tool.pyのget_current_time関数を使用
            params = {"format": format}
            return get_current_time(params)

        @self.mcp.tool('echo')
        def echo_wrapper(text: str) -> dict:
            """
            入力されたテキストをそのまま返します

            Args:
                text: エコーするテキスト
            """
            # example_tool.pyのecho関数を使用
            params = {"text": text}
            return echo(params)

        self.logger.info("サンプルツールを登録しました")

    def _register_rag_tools(self):
        """
        RAGツールを登録します
        """
        @self.mcp.tool('search')
        def search(
            query: str,
            limit: int = 5,
            with_context: bool = True,
            context_size: int = 1,
            full_document: bool = False
        ) -> dict:
            """
            ベクトル検索を行います

            Args:
                query: 検索クエリ
                limit: 返す結果の数（デフォルト: 5）
                with_context: 前後のチャンクも取得するかどうか（デフォルト: true）
                context_size: 前後に取得するチャンク数（デフォルト: 1）
                full_document: ドキュメント全体を取得するかどうか（デフォルト: false）
            """
            # rag_tools.pyのsearch_handlerを使用
            params = {
                "query": query,
                "limit": limit,
                "with_context": with_context,
                "context_size": context_size,
                "full_document": full_document
            }
            return search_handler(params, self.rag_service)

        @self.mcp.tool('get_document_count')
        def get_document_count() -> dict:
            """インデックス内のドキュメント数を取得します"""
            # rag_tools.pyのget_document_count_handlerを使用
            params = {}
            return get_document_count_handler(params, self.rag_service)

        self.logger.info("RAGツールを登録しました")

    def run(self, host: str = "127.0.0.1", port: int = 8000, path: str = "/mcp"):
        """
        HTTP MCPサーバーを起動します

        Args:
            host: サーバーのホスト（デフォルト: 127.0.0.1）
            port: サーバーのポート（デフォルト: 8000）
            path: MCPエンドポイントのパス（デフォルト: /mcp）
        """
        self.logger.info(f"HTTP MCPサーバー '{self.name}' を起動します")
        self.logger.info(f"URL: http://{host}:{port}{path}")

        try:
            self.mcp.run(
                transport="streamable-http",
                host=host,
                port=port,
                path=path,
                log_level="info"
            )
        except Exception as e:
            self.logger.error(f"サーバーの起動に失敗しました: {str(e)}")
            raise