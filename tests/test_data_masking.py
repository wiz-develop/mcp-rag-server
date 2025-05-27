"""
データマスキング機能のテストモジュール
"""

import os
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from document_processor import DocumentProcessor


class TestDataMasking:
    """データマスキング機能のテストクラス"""

    def test_masking_disabled_by_default(self):
        """デフォルトではマスキング機能が無効であることをテスト"""
        processor = DocumentProcessor()
        assert processor.masking_enabled is False

        test_text = "連絡先: test@example.com, 電話: 03-1234-5678"
        result = processor.apply_data_masking(test_text)
        assert result == test_text  # マスキングされないことを確認

    def test_masking_enabled(self):
        """マスキング機能が有効な場合のテスト"""
        processor = DocumentProcessor(masking_enabled=True)
        assert processor.masking_enabled is True

        test_text = "連絡先: test@example.com, 電話: 03-1234-5678"
        result = processor.apply_data_masking(test_text)

        # メールアドレスと電話番号がマスキングされることを確認
        assert "[MASKED_EMAIL]" in result
        assert "[MASKED_PHONE]" in result
        assert "test@example.com" not in result
        assert "03-1234-5678" not in result

    def test_email_masking(self):
        """メールアドレスのマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "test@example.com",
            "user.name@domain.co.jp",
            "admin@sub.domain.org",
        ]

        for email in test_cases:
            result = processor.apply_data_masking(email)
            assert "[MASKED_EMAIL]" in result
            assert email not in result

    def test_phone_masking(self):
        """電話番号のマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "03-1234-5678",
            "090-1234-5678",
            "0120-12-3456",
        ]

        for phone in test_cases:
            result = processor.apply_data_masking(phone)
            assert "[MASKED_PHONE]" in result
            assert phone not in result

    def test_credit_card_masking(self):
        """クレジットカード番号のマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "1234 5678 9012 3456",
            "1234-5678-9012-3456",
            "1234567890123456",
        ]

        for card in test_cases:
            result = processor.apply_data_masking(card)
            assert "[MASKED_CREDIT_CARD]" in result
            assert card not in result

    def test_ip_address_masking(self):
        """IPアドレスのマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
        ]

        for ip in test_cases:
            result = processor.apply_data_masking(ip)
            assert "[MASKED_IP]" in result
            assert ip not in result

    def test_url_masking(self):
        """URLのマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_cases = [
            "http://example.com",
            "https://www.example.com/path",
            "https://subdomain.example.com/path?param=value",
        ]

        for url in test_cases:
            result = processor.apply_data_masking(url)
            assert "[MASKED_URL]" in result
            assert url not in result

    def test_custom_masking_rule(self):
        """カスタムマスキングルールのテスト"""
        custom_rules = [
            {
                "name": "custom_number",
                "pattern": r"\b\d{3}-\d{3}-\d{3}\b",
                "replacement": "[MASKED_CUSTOM]",
                "description": "カスタム番号"
            }
        ]

        processor = DocumentProcessor(masking_enabled=True, custom_masking_rules=custom_rules)

        test_text = "カスタム番号: 123-456-789"
        result = processor.apply_data_masking(test_text)

        assert "[MASKED_CUSTOM]" in result
        assert "123-456-789" not in result

    def test_add_masking_rule(self):
        """実行時のマスキングルール追加をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 新しいルールを追加
        processor.add_masking_rule(
            name="test_pattern",
            pattern=r"TEST\d+",
            replacement="[MASKED_TEST]",
            description="テストパターン"
        )

        test_text = "これはTEST123の例です"
        result = processor.apply_data_masking(test_text)

        assert "[MASKED_TEST]" in result
        assert "TEST123" not in result

    def test_remove_masking_rule(self):
        """マスキングルールの削除をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 最初にメールアドレスがマスキングされることを確認
        test_text = "連絡先: test@example.com"
        result = processor.apply_data_masking(test_text)
        assert "[MASKED_EMAIL]" in result

        # emailルールを削除
        processor.remove_masking_rule("email")

        # 今度はマスキングされないことを確認
        result = processor.apply_data_masking(test_text)
        assert "test@example.com" in result
        assert "[MASKED_EMAIL]" not in result

    def test_list_masking_rules(self):
        """マスキングルールの一覧取得をテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        rules = processor.list_masking_rules()

        # デフォルトルールが含まれていることを確認
        rule_names = {rule["name"] for rule in rules}
        expected_rules = {"email", "phone_jp", "credit_card", "social_security_jp", "ip_address", "url"}

        assert expected_rules.issubset(rule_names)

    def test_complex_text_masking(self):
        """複数の機密情報を含む複雑なテキストのマスキングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        test_text = """
        顧客情報:
        - 名前: 田中太郎
        - メール: tanaka@example.com
        - 電話: 03-1234-5678
        - クレジットカード: 1234-5678-9012-3456
        - IP: 192.168.1.100
        - ウェブサイト: https://example.com/profile
        """

        result = processor.apply_data_masking(test_text)

        # 全ての機密情報がマスキングされていることを確認
        assert "[MASKED_EMAIL]" in result
        assert "[MASKED_PHONE]" in result
        assert "[MASKED_CREDIT_CARD]" in result
        assert "[MASKED_IP]" in result
        assert "[MASKED_URL]" in result

        # 元の機密情報が残っていないことを確認
        assert "tanaka@example.com" not in result
        assert "03-1234-5678" not in result
        assert "1234-5678-9012-3456" not in result
        assert "192.168.1.100" not in result
        assert "https://example.com/profile" not in result

        # 一般的な情報は残っていることを確認
        assert "田中太郎" in result

    def test_env_masking_rule_loading(self):
        """環境変数からのマスキングルール読み込みをテスト"""
        # 環境変数を設定
        os.environ["MASK_RULE_COMPANY_PATTERN"] = r"株式会社[^\s]+"
        os.environ["MASK_RULE_COMPANY_REPLACEMENT"] = "[MASKED_COMPANY]"
        os.environ["MASK_RULE_COMPANY_DESCRIPTION"] = "会社名"

        try:
            processor = DocumentProcessor(masking_enabled=True)

            test_text = "株式会社テスト"
            result = processor.apply_data_masking(test_text)

            # 既存のルールと競合してCOMPANY1が適用される場合がある
            assert "[MASKED_COMPANY" in result  # COMPANYまたはCOMPANY1が適用される
            assert "株式会社テスト" not in result

            # ルールリストに含まれていることを確認
            rules = processor.list_masking_rules()
            rule_names = {rule["name"] for rule in rules}
            assert "company" in rule_names

        finally:
            # 環境変数をクリーンアップ
            for key in ["MASK_RULE_COMPANY_PATTERN", "MASK_RULE_COMPANY_REPLACEMENT", "MASK_RULE_COMPANY_DESCRIPTION"]:
                if key in os.environ:
                    del os.environ[key]

    def test_create_from_env(self):
        """環境変数からのDocumentProcessor作成をテスト"""
        # マスキング有効の環境変数を設定
        os.environ["MASKING_ENABLED"] = "true"

        try:
            processor = DocumentProcessor.create_from_env()
            assert processor.masking_enabled is True

        finally:
            # 環境変数をクリーンアップ
            if "MASKING_ENABLED" in os.environ:
                del os.environ["MASKING_ENABLED"]

        # マスキング無効のテスト
        os.environ["MASKING_ENABLED"] = "false"

        try:
            processor = DocumentProcessor.create_from_env()
            assert processor.masking_enabled is False

        finally:
            # 環境変数をクリーンアップ
            if "MASKING_ENABLED" in os.environ:
                del os.environ["MASKING_ENABLED"]

    def test_invalid_regex_pattern(self):
        """無効な正規表現パターンのエラーハンドリングをテスト"""
        processor = DocumentProcessor(masking_enabled=True)

        # 無効な正規表現パターンでルールを追加
        processor.add_masking_rule(
            name="invalid_pattern",
            pattern="[invalid regex",  # 閉じ括弧がない無効なパターン
            replacement="[MASKED]",
            description="無効なパターン"
        )

        test_text = "これはテストです"
        # エラーが発生しても処理が続行されることを確認
        result = processor.apply_data_masking(test_text)
        assert result == test_text  # 元のテキストが返される