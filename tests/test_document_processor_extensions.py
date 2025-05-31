"""
ドキュメントプロセッサの新しい拡張子対応のテスト
"""

import pytest
from src.document_processor import DocumentProcessor


class TestDocumentProcessorExtensions:
    """ドキュメントプロセッサの拡張子対応テスト"""

    def test_supported_extensions_contains_new_formats(self):
        """新しい拡張子がサポートされているかテスト"""
        processor = DocumentProcessor()

        # Excel形式
        assert ".xls" in processor.SUPPORTED_EXTENSIONS["office"]
        assert ".xlsx" in processor.SUPPORTED_EXTENSIONS["office"]

        # 画像形式
        assert ".jpg" in processor.SUPPORTED_EXTENSIONS["images"]
        assert ".jpeg" in processor.SUPPORTED_EXTENSIONS["images"]
        assert ".png" in processor.SUPPORTED_EXTENSIONS["images"]

        # オーディオ形式
        assert ".wav" in processor.SUPPORTED_EXTENSIONS["audio"]
        assert ".mp3" in processor.SUPPORTED_EXTENSIONS["audio"]

        # HTML形式
        assert ".html" in processor.SUPPORTED_EXTENSIONS["html"]

        # テキストベース形式
        assert ".csv" in processor.SUPPORTED_EXTENSIONS["text-based"]
        assert ".json" in processor.SUPPORTED_EXTENSIONS["text-based"]
        assert ".xml" in processor.SUPPORTED_EXTENSIONS["text-based"]

        # ZIP形式
        assert ".zip" in processor.SUPPORTED_EXTENSIONS["zip"]

    def test_all_supported_extensions_structure(self):
        """全てのサポート拡張子の構造をテスト"""
        processor = DocumentProcessor()

        expected_structure = {
            "text": [".txt", ".md", ".markdown"],
            "office": [".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx"],
            "pdf": [".pdf"],
            "images": [".jpg", ".jpeg", ".png"],
            "audio": [".wav", ".mp3"],
            "html": [".html"],
            "text-based": [".csv", ".json", ".xml"],
            "zip": [".zip"],
        }

        assert processor.SUPPORTED_EXTENSIONS == expected_structure

    def test_file_extension_categorization(self):
        """ファイル拡張子の分類が正しいかテスト"""
        processor = DocumentProcessor()

        # テキストファイル
        text_extensions = processor.SUPPORTED_EXTENSIONS["text"]
        assert all(ext.startswith(".") for ext in text_extensions)

        # オフィスファイル（Excel含む）
        office_extensions = processor.SUPPORTED_EXTENSIONS["office"]
        assert ".xls" in office_extensions
        assert ".xlsx" in office_extensions
        assert ".ppt" in office_extensions
        assert ".doc" in office_extensions

        # 画像ファイル
        image_extensions = processor.SUPPORTED_EXTENSIONS["images"]
        assert ".jpg" in image_extensions
        assert ".jpeg" in image_extensions
        assert ".png" in image_extensions

        # オーディオファイル
        audio_extensions = processor.SUPPORTED_EXTENSIONS["audio"]
        assert ".wav" in audio_extensions
        assert ".mp3" in audio_extensions

        # HTMLファイル
        html_extensions = processor.SUPPORTED_EXTENSIONS["html"]
        assert ".html" in html_extensions

        # テキストベースファイル
        text_based_extensions = processor.SUPPORTED_EXTENSIONS["text-based"]
        assert ".csv" in text_based_extensions
        assert ".json" in text_based_extensions
        assert ".xml" in text_based_extensions

        # ZIPファイル
        zip_extensions = processor.SUPPORTED_EXTENSIONS["zip"]
        assert ".zip" in zip_extensions

    def test_processor_recognizes_new_extensions(self):
        """プロセッサが新しい拡張子を認識するかテスト"""
        processor = DocumentProcessor()

        # 全サポート拡張子を取得
        all_extensions = []
        for ext_list in processor.SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(ext_list)

        # 新しい拡張子が含まれているか確認
        # Excel形式
        assert ".xls" in all_extensions
        assert ".xlsx" in all_extensions

        # 画像形式
        assert ".jpg" in all_extensions
        assert ".jpeg" in all_extensions
        assert ".png" in all_extensions

        # オーディオ形式
        assert ".wav" in all_extensions
        assert ".mp3" in all_extensions

        # HTML形式
        assert ".html" in all_extensions

        # テキストベース形式
        assert ".csv" in all_extensions
        assert ".json" in all_extensions
        assert ".xml" in all_extensions

        # ZIP形式
        assert ".zip" in all_extensions