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
        
        # オーディオ形式
        assert ".wav" in processor.SUPPORTED_EXTENSIONS["audio"]
        assert ".mp3" in processor.SUPPORTED_EXTENSIONS["audio"]

    def test_all_supported_extensions_structure(self):
        """全てのサポート拡張子の構造をテスト"""
        processor = DocumentProcessor()
        
        expected_structure = {
            "text": [".txt", ".md", ".markdown"],
            "office": [".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx"],
            "pdf": [".pdf"],
            "audio": [".wav", ".mp3"],
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
        
        # オーディオファイル
        audio_extensions = processor.SUPPORTED_EXTENSIONS["audio"]
        assert ".wav" in audio_extensions
        assert ".mp3" in audio_extensions

    def test_processor_recognizes_new_extensions(self):
        """プロセッサが新しい拡張子を認識するかテスト"""
        processor = DocumentProcessor()
        
        # 全サポート拡張子を取得
        all_extensions = []
        for ext_list in processor.SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(ext_list)
        
        # 新しい拡張子が含まれているか確認
        assert ".xls" in all_extensions
        assert ".xlsx" in all_extensions
        assert ".wav" in all_extensions
        assert ".mp3" in all_extensions