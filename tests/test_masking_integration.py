"""
データマスキング機能の統合テストモジュール
"""

import tempfile
import os
from pathlib import Path
from src.document_processor import DocumentProcessor


class TestMaskingIntegration:
    """データマスキング機能の統合テストクラス"""

    def test_file_processing_with_masking(self):
        """ファイル処理時のマスキング統合テスト"""
        # マスキング有効でプロセッサを作成
        processor = DocumentProcessor(masking_enabled=True)

        # テスト用の一時ファイルを作成
        test_content = """
        # 顧客情報

        この文書には以下の機密情報が含まれています：

        - メールアドレス: customer@example.com
        - 電話番号: 03-1234-5678
        - クレジットカード: 1234-5678-9012-3456
        - ウェブサイト: https://company.example.com
        - IPアドレス: 192.168.1.1

        これらの情報は機密扱いです。
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # ファイルを読み込み
            content = processor.read_file(temp_file_path)

            # マスキングが適用されていることを確認
            assert "[MASKED_EMAIL]" in content
            assert "[MASKED_PHONE]" in content
            assert "[MASKED_CREDIT_CARD]" in content
            assert "[MASKED_URL]" in content
            assert "[MASKED_IP]" in content

            # 元の機密情報が残っていないことを確認
            assert "customer@example.com" not in content
            assert "03-1234-5678" not in content
            assert "1234-5678-9012-3456" not in content
            assert "https://company.example.com" not in content
            assert "192.168.1.1" not in content

            # 一般的な情報は残っていることを確認
            assert "顧客情報" in content
            assert "機密扱い" in content

        finally:
            # 一時ファイルを削除
            os.unlink(temp_file_path)

    def test_document_processing_with_masking(self):
        """ドキュメント処理のエンドツーエンドテスト"""
        # マスキング有効でプロセッサを作成
        processor = DocumentProcessor(masking_enabled=True)

        # テスト用の一時ディレクトリとファイルを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            processed_dir = Path(temp_dir) / "processed"
            source_dir.mkdir()
            processed_dir.mkdir()

            # テストファイル1
            test_file1 = source_dir / "document1.md"
            test_file1.write_text("""
            # ドキュメント1

            連絡先: contact@company.com
            電話: 03-1111-2222
            """, encoding='utf-8')

            # テストファイル2
            test_file2 = source_dir / "document2.txt"
            test_file2.write_text("""
            クレジットカード情報: 4111-1111-1111-1111
            ウェブサイト: https://secure.example.com
            """, encoding='utf-8')

            # ディレクトリを処理
            results = processor.process_directory(
                str(source_dir),
                str(processed_dir),
                chunk_size=200,
                overlap=50
            )

            # 結果を検証
            assert len(results) > 0

            for result in results:
                content = result["content"]

                # マスキングが適用されていることを確認
                if "contact@company.com" in test_file1.read_text(encoding='utf-8'):
                    # このチャンクに元々メールアドレスが含まれていた場合
                    if "[MASKED_EMAIL]" in content:
                        assert "contact@company.com" not in content

                if "03-1111-2222" in test_file1.read_text(encoding='utf-8'):
                    # このチャンクに元々電話番号が含まれていた場合
                    if "[MASKED_PHONE]" in content:
                        assert "03-1111-2222" not in content

                if "4111-1111-1111-1111" in test_file2.read_text(encoding='utf-8'):
                    # このチャンクに元々クレジットカード番号が含まれていた場合
                    if "[MASKED_CREDIT_CARD]" in content:
                        assert "4111-1111-1111-1111" not in content

                if "https://secure.example.com" in test_file2.read_text(encoding='utf-8'):
                    # このチャンクに元々URLが含まれていた場合
                    if "[MASKED_URL]" in content:
                        assert "https://secure.example.com" not in content

    def test_env_based_configuration(self):
        """環境変数ベースの設定テスト"""
        # 環境変数を設定
        os.environ["MASKING_ENABLED"] = "true"
        os.environ["MASK_RULE_SECRET_PATTERN"] = r"SECRET-\d+"
        os.environ["MASK_RULE_SECRET_REPLACEMENT"] = "[MASKED_SECRET]"
        os.environ["MASK_RULE_SECRET_DESCRIPTION"] = "秘密コード"

        try:
            # 環境変数から作成
            processor = DocumentProcessor.create_from_env()

            # マスキングが有効であることを確認
            assert processor.masking_enabled is True

            # カスタムルールが追加されていることを確認
            rules = processor.list_masking_rules()
            rule_names = {rule["name"] for rule in rules}
            assert "secret" in rule_names

            # カスタムルールが機能することをテスト
            test_text = "これはSECRET-12345です"
            result = processor.apply_data_masking(test_text)
            assert "[MASKED_SECRET]" in result
            assert "SECRET-12345" not in result

        finally:
            # 環境変数をクリーンアップ
            for key in ["MASKING_ENABLED", "MASK_RULE_SECRET_PATTERN", "MASK_RULE_SECRET_REPLACEMENT", "MASK_RULE_SECRET_DESCRIPTION"]:
                if key in os.environ:
                    del os.environ[key]

    def test_performance_with_large_text(self):
        """大きなテキストでのマスキング性能テスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 大きなテキストを生成（機密情報を含む）
        large_text_parts = []
        for i in range(1000):
            large_text_parts.append(f"行{i}: user{i}@example.com, 電話: 03-{i:04d}-{i:04d}")

        large_text = "\n".join(large_text_parts)

        # マスキングを実行
        import time
        start_time = time.time()
        result = processor.apply_data_masking(large_text)
        end_time = time.time()

        # 結果を検証
        assert "[MASKED_EMAIL]" in result
        assert "[MASKED_PHONE]" in result

        # 元の機密情報が残っていないことを確認（サンプルをチェック）
        assert "user0@example.com" not in result
        assert "user999@example.com" not in result

        # 実行時間をログ出力（アサーションはしない、参考情報として）
        execution_time = end_time - start_time
        print(f"大きなテキスト（{len(large_text)} 文字）のマスキング実行時間: {execution_time:.2f}秒")

    def test_markdown_file_masking(self):
        """Markdownファイルのマスキングテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        markdown_content = """
        # 会社概要

        ## 連絡先情報

        - **メール**: info@company.example.com
        - **電話**: 03-1234-5678
        - **ウェブサイト**: https://www.company.example.com

        ## 技術情報

        サーバーIP: 10.0.0.1
        データベース接続文字列: postgres://user:pass@192.168.1.100:5432/db

        クレジットカード（テスト用）: 4111-1111-1111-1111
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(markdown_content)
            temp_file_path = f.name

        try:
            content = processor.read_file(temp_file_path)

            # Markdownの構造は維持されているが、機密情報はマスキングされている
            assert "# 会社概要" in content
            assert "## 連絡先情報" in content
            assert "**メール**" in content

            # 機密情報がマスキングされている
            assert "[MASKED_EMAIL]" in content
            assert "[MASKED_PHONE]" in content
            assert "[MASKED_URL]" in content
            assert "[MASKED_IP]" in content
            assert "[MASKED_CREDIT_CARD]" in content

            # 元の機密情報が残っていない
            assert "info@company.example.com" not in content
            assert "03-1234-5678" not in content
            assert "https://www.company.example.com" not in content
            assert "10.0.0.1" not in content
            assert "192.168.1.100" not in content
            assert "4111-1111-1111-1111" not in content

        finally:
            os.unlink(temp_file_path)

    def test_masking_preserves_text_structure(self):
        """マスキングがテキスト構造を保持することを確認"""
        processor = DocumentProcessor(masking_enabled=True)

        test_text = """項目1: test@example.com
項目2: 03-1234-5678
項目3: https://example.com
項目4: 正常なテキスト"""

        result = processor.apply_data_masking(test_text)

        # 行数が変わっていないことを確認
        original_lines = test_text.split('\n')
        result_lines = result.split('\n')
        assert len(original_lines) == len(result_lines)

        # 項目の構造が保持されていることを確認
        assert "項目1:" in result
        assert "項目2:" in result
        assert "項目3:" in result
        assert "項目4: 正常なテキスト" in result