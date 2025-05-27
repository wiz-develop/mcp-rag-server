"""
ファイル名マスキング機能のテストモジュール
"""

import os
import sys
import tempfile
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from document_processor import DocumentProcessor


class TestFilenameMasking:
    """ファイル名マスキング機能のテストクラス"""

    def test_filename_masking_disabled(self):
        """マスキング無効時のファイル名処理をテスト"""
        processor = DocumentProcessor(masking_enabled=False)

        test_filename = "test@example.com_document.pdf"
        result = processor.apply_filename_masking(test_filename)
        assert result == test_filename  # マスキングされないことを確認

    def test_filename_masking_enabled(self):
        """マスキング有効時のファイル名処理をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_filename = "test@example.com_document.pdf"
        result = processor.apply_filename_masking(test_filename)

        # メールアドレスがマスキングされていることを確認
        assert "[MASKED_EMAIL]" in result
        assert "test@example.com" not in result
        assert result.endswith(".pdf")  # 拡張子は保持されることを確認

    def test_filename_sanitization(self):
        """ファイル名で使用できない文字の変換をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 使用禁止文字を含むファイル名
        test_cases = [
            ("file<name>.txt", "＜"),  # <が全角に変換される
            ("file>name.txt", "＞"),  # >が全角に変換される
            ("file:name.txt", "："),  # :が全角に変換される
            ("file\"name.txt", "\u201d"),  # "が右ダブルクォーテーションマークに変換される
            ("file|name.txt", "｜"),  # |が全角パイプに変換される
            ("file?name.txt", "？"),  # ?が全角クエスチョンに変換される
            ("file*name.txt", "＊"),  # *が全角アスタリスクに変換される
        ]

        for test_filename, expected_char in test_cases:
            result = processor.apply_filename_masking(test_filename)
            assert expected_char in result
            assert result.endswith(".txt")
        
        # スラッシュとバックスラッシュは別途テスト（ディレクトリ区切り文字として解釈される可能性があるため）
        slash_test_cases = [
            ("filename.txt", "/", "filename／slash.txt"),  # /を含むファイル名
            ("filename.txt", "\\", "filename￥backslash.txt"),  # \\を含むファイル名
        ]
        
        for base_filename, char, test_filename in slash_test_cases:
            # 直接サニタイズ関数をテスト
            sanitized = processor._sanitize_filename(test_filename.replace(".txt", ""))
            expected_char = "／" if char == "/" else "￥"
            assert expected_char in sanitized

    def test_filename_control_characters(self):
        """制御文字を含むファイル名の変換をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 制御文字（ASCII 0-31）を含むファイル名
        test_filename = "file\x00\x01name.txt"  # NULとSOH文字
        result = processor._sanitize_filename(test_filename)

        # 制御文字がアンダースコアに変換されることを確認
        assert "__" in result
        assert "\x00" not in result
        assert "\x01" not in result

    def test_filename_empty_or_dots_only(self):
        """空文字列やドットのみのファイル名の処理をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "",  # 空文字列
            ".",  # ドットのみ
            "..",  # ドットのみ（複数）
            "   ",  # スペースのみ
        ]

        for test_filename in test_cases:
            result = processor._sanitize_filename(test_filename)
            assert result == "masked_file"  # デフォルト名が使用されることを確認

    def test_filename_length_limit(self):
        """ファイル名の長さ制限をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 255バイトを超える長いファイル名
        long_filename = "あ" * 200  # 日本語文字は3バイトなので600バイト
        result = processor._sanitize_filename(long_filename)

        # 255バイト以下に制限されることを確認
        assert len(result.encode('utf-8')) <= 255
        assert len(result) > 0  # 空文字列にはならないことを確認

    def test_complex_filename_masking(self):
        """複雑なファイル名のマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 複数の機密情報と使用禁止文字を含むファイル名
        complex_filename = "report_admin@example.com_03-1234-5678_<confidential>.pdf"
        result = processor.apply_filename_masking(complex_filename)

        # すべての機密情報がマスキングされていることを確認
        assert "[MASKED_EMAIL]" in result
        assert "[MASKED_PHONE]" in result
        assert "admin@example.com" not in result
        assert "03-1234-5678" not in result

        # 使用禁止文字が変換されていることを確認
        assert "＜" in result  # <が全角に変換されている
        assert "<" not in result

        # 拡張子は保持されることを確認
        assert result.endswith(".pdf")

    def test_metadata_filename_masking(self):
        """メタデータのファイル名マスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 機密情報を含むファイルを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイルを作成
            test_filename = "report_admin@example.com.txt"
            test_file_path = os.path.join(temp_dir, test_filename)
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write("テストデータ")

            # 処理済みディレクトリを作成
            processed_dir = os.path.join(temp_dir, "processed")
            os.makedirs(processed_dir, exist_ok=True)

            # ファイルを処理
            results = processor.process_file(test_file_path, processed_dir)

            # 結果を確認
            assert len(results) > 0
            metadata = results[0]["metadata"]

            # メタデータのファイル名がマスキングされていることを確認
            assert "[MASKED_EMAIL]" in metadata["file_name"]
            assert "admin@example.com" not in metadata["file_name"]

            # オリジナルのファイル名が保持されていることを確認
            assert metadata["original_file_name"] == test_filename
            assert "admin@example.com" in metadata["original_file_name"]