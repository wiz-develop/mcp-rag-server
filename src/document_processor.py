"""
ドキュメント処理モジュール

マークダウン、テキスト、パワーポイント、PDFなどのファイルの読み込みと解析、チャンク分割を行います。
"""

import logging
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import time

import markitdown


class DocumentProcessor:
    """
    ドキュメント処理クラス

    マークダウン、テキスト、パワーポイント、PDFなどのファイルの読み込みと解析、チャンク分割を行います。
    データマスキング機能を含みます。

    Attributes:
        logger: ロガー
        masking_enabled: マスキング機能を有効にするかどうか
        masking_rules: マスキングルールのリスト
    """

    # サポートするファイル拡張子
    SUPPORTED_EXTENSIONS = {
        "text": [".txt", ".md", ".markdown"],
        "office": [".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx"],
        "pdf": [".pdf"],
        "images": [".jpg", ".jpeg", ".png"],
        "audio": [".wav", ".mp3"],
        "html": [".html"],
        "text-based": [".csv", ".json", ".xml"],
        "zip": [".zip"],
    }

    # デフォルトのマスキングルール
    DEFAULT_MASKING_RULES = [
        {
            "name": "email",
            "pattern": r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
            "replacement": "[MASKED_EMAIL]",
            "description": "メールアドレス"
        },
        {
            "name": "credit_card",
            "pattern": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            "replacement": "[MASKED_CREDIT_CARD]",
            "description": "クレジットカード番号"
        },
        {
            "name": "phone_jp",
            "pattern": r'(?:0\d{1,4}|0\d{2,3}|\d{2,4})-\d{2,4}-\d{4}',
            "replacement": "[MASKED_PHONE]",
            "description": "日本の電話番号"
        },
        {
            "name": "social_security_jp",
            "pattern": r'\d{4}-\d{2}-\d{6}',
            "replacement": "[MASKED_SSN]",
            "description": "マイナンバー"
        },
        {
            "name": "ip_address",
            "pattern": r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}',
            "replacement": "[MASKED_IP]",
            "description": "IPアドレス"
        },
        {
            "name": "url",
            "pattern": r'https?://[^\s<>"]+',
            "replacement": "[MASKED_URL]",
            "description": "URL"
        }
    ]

    def __init__(self, masking_enabled: bool = False, custom_masking_rules: Optional[List[Dict[str, str]]] = None):
        """
        DocumentProcessorのコンストラクタ

        Args:
            masking_enabled: マスキング機能を有効にするかどうか（デフォルト: False）
            custom_masking_rules: カスタムマスキングルールのリスト（オプション）
        """
        # ロガーの設定
        self.logger = logging.getLogger("document_processor")
        self.logger.setLevel(logging.INFO)

        # マスキング機能の設定
        self.masking_enabled = masking_enabled
        self.masking_rules = self.DEFAULT_MASKING_RULES.copy()

        # カスタムマスキングルールを追加
        if custom_masking_rules:
            self.masking_rules.extend(custom_masking_rules)

        # 環境変数からマスキングルールを読み込み
        self._load_masking_rules_from_env()

        if self.masking_enabled:
            self.logger.info(f"データマスキング機能が有効です（{len(self.masking_rules)} ルール）")

    def _load_masking_rules_from_env(self) -> None:
        """
        環境変数からマスキングルールを読み込みます。

        環境変数の形式:
        - MASK_RULE_<rule_name>_PATTERN: マスキングパターン（正規表現）
        - MASK_RULE_<rule_name>_REPLACEMENT: 置換文字列
        - MASK_RULE_<rule_name>_DESCRIPTION: ルールの説明（オプション）

        例:
        - MASK_RULE_COMPANY_PATTERN="株式会社[^\\s]+"
        - MASK_RULE_COMPANY_REPLACEMENT="[MASKED_COMPANY]"
        - MASK_RULE_COMPANY_DESCRIPTION="会社名"
        """
        import os

        # 環境変数からマスキングルールを抽出
        env_rules = {}
        for key, value in os.environ.items():
            if key.startswith("MASK_RULE_"):
                parts = key.split("_", 3)  # MASK_RULE_<rule_name>_<field>
                if len(parts) >= 4:
                    rule_name = parts[2].lower()
                    field = parts[3].lower()

                    if rule_name not in env_rules:
                        env_rules[rule_name] = {}

                    env_rules[rule_name][field] = value

        # 完全なルール（patternとreplacementが両方ある）のみを追加
        for rule_name, rule_data in env_rules.items():
            if "pattern" in rule_data and "replacement" in rule_data:
                # 既存のルールと重複していないかチェック
                existing_names = {rule["name"] for rule in self.masking_rules}
                if rule_name not in existing_names:
                    self.masking_rules.append({
                        "name": rule_name,
                        "pattern": rule_data["pattern"],
                        "replacement": rule_data["replacement"],
                        "description": rule_data.get("description", f"環境変数で定義されたカスタムルール: {rule_name}")
                    })
                    self.logger.info(f"環境変数からマスキングルール '{rule_name}' を追加しました")
                else:
                    self.logger.warning(f"マスキングルール '{rule_name}' は既に存在するため、環境変数からの追加をスキップしました")
            else:
                missing_fields = []
                if "pattern" not in rule_data:
                    missing_fields.append("PATTERN")
                if "replacement" not in rule_data:
                    missing_fields.append("REPLACEMENT")
                self.logger.warning(f"環境変数のマスキングルール '{rule_name}' に必要なフィールドが不足しています: {', '.join(missing_fields)}")

    @classmethod
    def create_from_env(cls) -> 'DocumentProcessor':
        """
        環境変数からDocumentProcessorを作成します。

        環境変数:
        - MASKING_ENABLED: マスキング機能を有効にするかどうか（"true"/"false", デフォルト: "false"）

        Returns:
            DocumentProcessorのインスタンス
        """
        import os

        # 環境変数からマスキング設定を取得
        masking_enabled = os.environ.get("MASKING_ENABLED", "false").lower() == "true"

        return cls(masking_enabled=masking_enabled)

    def apply_data_masking(self, text: str) -> str:
        """
        テキストにデータマスキングを適用します。

        Args:
            text: マスキング対象のテキスト

        Returns:
            マスキング後のテキスト
        """
        if not self.masking_enabled:
            return text

        masked_text = text
        masked_count = 0

        for rule in self.masking_rules:
            try:
                pattern = rule["pattern"]
                replacement = rule["replacement"]
                rule_name = rule["name"]

                # マッチ数を数える
                matches = re.findall(pattern, masked_text)
                if matches:
                    rule_match_count = len(matches)
                    masked_count += rule_match_count

                    # マスキングを適用
                    masked_text = re.sub(pattern, replacement, masked_text)

                    self.logger.debug(f"マスキングルール '{rule_name}': {rule_match_count} 個の項目をマスキングしました")

            except re.error as e:
                self.logger.error(f"マスキングルール '{rule_name}' の正規表現エラー: {str(e)}")
                continue

        if masked_count > 0:
            self.logger.info(f"合計 {masked_count} 個の機密情報をマスキングしました")

        return masked_text

    def apply_filename_masking(self, filename: str) -> str:
        """
        ファイル名にデータマスキングを適用します。

        Args:
            filename: マスキング対象のファイル名

        Returns:
            マスキング後のファイル名（ファイルシステムで使用可能な文字に変換）
        """
        if not self.masking_enabled:
            return filename

        # ファイル拡張子を分離
        path_obj = Path(filename)
        stem = path_obj.stem  # 拡張子を除いたファイル名
        suffix = path_obj.suffix  # 拡張子

        # ファイル名本体にマスキングを適用
        masked_stem = self.apply_data_masking(stem)

        # ファイル名で使用できない文字を変換
        sanitized_stem = self._sanitize_filename(masked_stem)

        # 拡張子と結合して返す
        return sanitized_stem + suffix

    def _sanitize_filename(self, filename: str) -> str:
        """
        ファイル名で使用できない文字を安全な文字に変換します。

        Args:
            filename: 変換対象のファイル名

        Returns:
            安全なファイル名
        """
        # Windows/Unix共通で使用できない文字とその置き換え
        invalid_chars = {
            '<': '＜',  # 全角に変換
            '>': '＞',
            ':': '：',
            '"': '”',  # 右ダブルクォートーションマーク
            '/': '／',  # 全角スラッシュ
            '\\': '＼',  # 全角バックスラッシュ
            '|': '｜',  # 全角パイプ
            '?': '？',  # 全角クエスチョン
            '*': '＊',  # 全角アスタリスク
        }

        sanitized = filename
        for invalid_char, replacement in invalid_chars.items():
            sanitized = sanitized.replace(invalid_char, replacement)

        # 制御文字（ASCII 0-31）をアンダースコアに変換
        sanitized = ''.join(char if ord(char) >= 32 else '_' for char in sanitized)

        # ファイル名の最大長を制限（255バイト）
        if len(sanitized.encode('utf-8')) > 255:
            # UTF-8で255バイト以下にする
            while len(sanitized.encode('utf-8')) > 255 and len(sanitized) > 1:
                sanitized = sanitized[:-1]

        # 空文字列やドットのみの場合はデフォルト名を使用
        if not sanitized or sanitized.replace('.', '').strip() == '':
            sanitized = 'masked_file'

        return sanitized

    def add_masking_rule(self, name: str, pattern: str, replacement: str, description: str = "") -> None:
        """
        新しいマスキングルールを追加します。

        Args:
            name: ルールの名前
            pattern: 正規表現パターン
            replacement: 置換文字列
            description: ルールの説明（オプション）
        """
        # 同じ名前のルールが既に存在する場合は更新
        for i, rule in enumerate(self.masking_rules):
            if rule["name"] == name:
                self.masking_rules[i] = {
                    "name": name,
                    "pattern": pattern,
                    "replacement": replacement,
                    "description": description
                }
                self.logger.info(f"マスキングルール '{name}' を更新しました")
                return

        # 新しいルールを追加
        self.masking_rules.append({
            "name": name,
            "pattern": pattern,
            "replacement": replacement,
            "description": description
        })
        self.logger.info(f"マスキングルール '{name}' を追加しました")

    def remove_masking_rule(self, name: str) -> bool:
        """
        マスキングルールを削除します。

        Args:
            name: 削除するルールの名前

        Returns:
            削除に成功した場合はTrue、ルールが見つからない場合はFalse
        """
        for i, rule in enumerate(self.masking_rules):
            if rule["name"] == name:
                del self.masking_rules[i]
                self.logger.info(f"マスキングルール '{name}' を削除しました")
                return True

        self.logger.warning(f"マスキングルール '{name}' が見つかりません")
        return False

    def list_masking_rules(self) -> List[Dict[str, str]]:
        """
        現在のマスキングルールのリストを取得します。

        Returns:
            マスキングルールのリスト
        """
        return self.masking_rules.copy()

    def read_file(self, file_path: str) -> str:
        """
        ファイルを読み込みます。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルの内容

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            IOError: ファイルの読み込みに失敗した場合
        """
        try:
            # ファイル拡張子を取得
            ext = Path(file_path).suffix.lower()

            # テキストファイル（マークダウン含む）の場合
            if ext in self.SUPPORTED_EXTENSIONS["text"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # NUL文字を削除
                    content = content.replace("\x00", "")
                    # データマスキングを適用
                    content = self.apply_data_masking(content)
                self.logger.info(f"テキストファイル '{file_path}' を読み込みました")
                return content

            # パワーポイント、Office系、PDF、画像、オーディオファイル、HTML、テキストベース系、Zipの場合はmarkitdownを使用して変換
            elif (ext in self.SUPPORTED_EXTENSIONS["office"] or
                  ext in self.SUPPORTED_EXTENSIONS["pdf"] or
                  ext in self.SUPPORTED_EXTENSIONS["images"] or
                  ext in self.SUPPORTED_EXTENSIONS["audio"] or
                  ext in self.SUPPORTED_EXTENSIONS["html"] or
                  ext in self.SUPPORTED_EXTENSIONS["text-based"] or
                  ext in self.SUPPORTED_EXTENSIONS["zip"]):
                return self.convert_to_markdown(file_path)

            # サポートしていない拡張子の場合
            else:
                self.logger.warning(f"サポートしていないファイル形式です: {file_path}")
                return ""

        except FileNotFoundError:
            self.logger.error(f"ファイル '{file_path}' が見つかりません")
            raise
        except IOError as e:
            self.logger.error(f"ファイル '{file_path}' の読み込みに失敗しました: {str(e)}")
            raise

    def convert_to_markdown(self, file_path: str) -> str:
        """
        パワーポイント、Word、PDFなどのファイルをマークダウンに変換します。

        Args:
            file_path: ファイルのパス

        Returns:
            マークダウンに変換された内容

        Raises:
            Exception: 変換に失敗した場合
        """
        try:
            # ファイルURIを作成
            file_uri = f"file://{os.path.abspath(file_path)}"

            # markitdownを使用して変換
            markdown_content = markitdown.MarkItDown().convert_uri(file_uri).markdown
            # NUL文字を削除
            markdown_content = markdown_content.replace("\x00", "")
            # データマスキングを適用
            markdown_content = self.apply_data_masking(markdown_content)

            self.logger.info(f"ファイル '{file_path}' をマークダウンに変換しました")
            return markdown_content
        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' のマークダウン変換に失敗しました: {str(e)}")
            raise

    def split_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        テキストをチャンクに分割します。

        Args:
            text: 分割するテキスト
            chunk_size: チャンクサイズ（文字数）
            overlap: チャンク間のオーバーラップ（文字数）

        Returns:
            チャンクのリスト
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # 文の途中で切らないように調整
            if end < text_length:
                # 次の改行または句点を探す
                next_newline = text.find("\n", end)
                next_period = text.find("。", end)

                if next_newline != -1 and (next_period == -1 or next_newline < next_period):
                    end = next_newline + 1  # 改行を含める
                elif next_period != -1:
                    end = next_period + 1  # 句点を含める

            chunks.append(text[start:end])
            start = end - overlap if end - overlap > start else end

            # 終了条件
            if start >= text_length:
                break

        self.logger.info(f"テキストを {len(chunks)} チャンクに分割しました")
        return chunks

    def calculate_file_hash(self, file_path: str) -> str:
        """
        ファイルのハッシュ値を計算します。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルのSHA-256ハッシュ値
        """
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' のハッシュ計算に失敗しました: {str(e)}")
            # エラーが発生した場合は、タイムスタンプをハッシュとして使用
            return f"timestamp-{int(time.time())}"

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        ファイルのメタデータを取得します。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルのメタデータ（ハッシュ値、最終更新日時など）
        """
        file_stat = os.stat(file_path)
        return {
            "hash": self.calculate_file_hash(file_path),
            "mtime": file_stat.st_mtime,
            "size": file_stat.st_size,
            "path": file_path,
        }

    def load_file_registry(self, processed_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        処理済みファイルのレジストリを読み込みます。

        Args:
            processed_dir: 処理済みファイルを保存するディレクトリのパス

        Returns:
            処理済みファイルのレジストリ（ファイルパスをキーとするメタデータの辞書）
        """
        registry_path = Path(processed_dir) / "file_registry.json"
        if not registry_path.exists():
            return {}

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"ファイルレジストリの読み込みに失敗しました: {str(e)}")
            return {}

    def save_file_registry(self, processed_dir: str, registry: Dict[str, Dict[str, Any]]) -> None:
        """
        処理済みファイルのレジストリを保存します。

        Args:
            processed_dir: 処理済みファイルを保存するディレクトリのパス
            registry: 処理済みファイルのレジストリ
        """
        registry_path = Path(processed_dir) / "file_registry.json"
        try:
            # 処理済みディレクトリが存在しない場合は作成
            os.makedirs(Path(processed_dir), exist_ok=True)

            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
            self.logger.info(f"ファイルレジストリを保存しました: {registry_path}")
        except Exception as e:
            self.logger.error(f"ファイルレジストリの保存に失敗しました: {str(e)}")

    def process_file(
        self, file_path: str, processed_dir: str, chunk_size: int = 500, overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        ファイルを処理します。

        Args:
            file_path: ファイルのパス
            processed_dir: 処理済みファイルを保存するディレクトリのパス
            chunk_size: チャンクサイズ（文字数）
            overlap: チャンク間のオーバーラップ（文字数）

        Returns:
            処理結果のリスト（各要素はチャンク情報を含む辞書）
        """
        try:
            # ファイルを読み込む
            content = self.read_file(file_path)
            if not content:
                return []

            # ファイルパスからディレクトリ構造を取得
            file_path_obj = Path(file_path)
            relative_path = file_path_obj.relative_to(Path(file_path_obj.parts[0]) / Path(file_path_obj.parts[1]))
            parent_dirs = relative_path.parent.parts

            # ディレクトリ名をサフィックスとして使用
            dir_suffix = "_".join(parent_dirs) if parent_dirs else ""

            # 処理済みファイル名を生成（マスキング適用）
            masked_stem = self.apply_filename_masking(file_path_obj.stem + file_path_obj.suffix).replace(file_path_obj.suffix, '')
            masked_dir_suffix = self._sanitize_filename(self.apply_data_masking(dir_suffix)) if dir_suffix else ""
            processed_file_name = f"{masked_stem}{('_' + masked_dir_suffix) if masked_dir_suffix else ''}.md"
            processed_file_path = Path(processed_dir) / processed_file_name

            # 処理済みディレクトリが存在しない場合は作成
            os.makedirs(Path(processed_dir), exist_ok=True)

            # 処理済みファイルに書き込む
            with open(processed_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"処理済みファイルを保存しました: {processed_file_path}")

            # チャンクに分割
            chunks = self.split_into_chunks(content, chunk_size, overlap)

            # 結果を作成
            results = []
            for i, chunk in enumerate(chunks):
                document_id = f"{processed_file_name}_{i}"
                results.append(
                    {
                        "document_id": document_id,
                        "content": chunk,
                        "file_path": str(processed_file_path),
                        "original_file_path": file_path,
                        "chunk_index": i,
                        "metadata": {
                            "file_name": self.apply_filename_masking(file_path_obj.name),
                            "directory": self.apply_data_masking(str(file_path_obj.parent)),
                            "directory_suffix": self.apply_data_masking(dir_suffix),
                            "original_file_name": file_path_obj.name,
                            "original_directory": str(file_path_obj.parent),
                            "original_directory_suffix": dir_suffix,
                        },
                    }
                )

            self.logger.info(f"ファイル '{file_path}' を処理しました（{len(results)} チャンク）")
            return results

        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' の処理中にエラーが発生しました: {str(e)}")
            raise

    def process_directory(
        self, source_dir: str, processed_dir: str, chunk_size: int = 500, overlap: int = 100, incremental: bool = False
    ) -> List[Dict[str, Any]]:
        """
        ディレクトリ内のファイルを処理します。

        Args:
            source_dir: 原稿ファイルが含まれるディレクトリのパス
            processed_dir: 処理済みファイルを保存するディレクトリのパス
            chunk_size: チャンクサイズ（文字数）
            overlap: チャンク間のオーバーラップ（文字数）
            incremental: 差分のみを処理するかどうか

        Returns:
            処理結果のリスト（各要素はチャンク情報を含む辞書）
        """
        results = []
        source_directory = Path(source_dir)

        if not source_directory.exists() or not source_directory.is_dir():
            self.logger.error(f"ディレクトリ '{source_dir}' が見つからないか、ディレクトリではありません")
            raise FileNotFoundError(f"ディレクトリ '{source_dir}' が見つからないか、ディレクトリではありません")

        # サポートするファイル拡張子を全て取得
        all_extensions = []
        for ext_list in self.SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(ext_list)

        # ファイルを検索
        files = []
        for ext in all_extensions:
            files.extend(list(source_directory.glob(f"**/*{ext}")))

        self.logger.info(f"ディレクトリ '{source_dir}' 内に {len(files)} 個のファイルが見つかりました")

        # 差分処理の場合、ファイルレジストリを読み込む
        if incremental:
            file_registry = self.load_file_registry(processed_dir)
            self.logger.info(f"ファイルレジストリから {len(file_registry)} 個のファイル情報を読み込みました")
        else:
            file_registry = {}

        # 処理対象のファイルを特定
        files_to_process = []
        for file_path in files:
            str_path = str(file_path)
            if incremental:
                # ファイルのメタデータを取得
                current_metadata = self.get_file_metadata(str_path)

                # レジストリに存在しない、またはハッシュ値が変更されている場合のみ処理
                if (
                    str_path not in file_registry
                    or file_registry[str_path]["hash"] != current_metadata["hash"]
                    or file_registry[str_path]["mtime"] != current_metadata["mtime"]
                    or file_registry[str_path]["size"] != current_metadata["size"]
                ):
                    files_to_process.append(file_path)
                    # レジストリを更新
                    file_registry[str_path] = current_metadata
            else:
                # 差分処理でない場合は全てのファイルを処理
                files_to_process.append(file_path)
                # レジストリを更新
                file_registry[str_path] = self.get_file_metadata(str_path)

        self.logger.info(f"処理対象のファイル数: {len(files_to_process)} / {len(files)}")

        # 各ファイルを処理
        for file_path in files_to_process:
            try:
                file_results = self.process_file(str(file_path), processed_dir, chunk_size, overlap)
                results.extend(file_results)
            except Exception as e:
                self.logger.error(f"ファイル '{file_path}' の処理中にエラーが発生しました: {str(e)}")
                # エラーが発生しても処理を続行
                continue

        # ファイルレジストリを保存
        self.save_file_registry(processed_dir, file_registry)

        self.logger.info(f"ディレクトリ '{source_dir}' 内のファイルを処理しました（合計 {len(results)} チャンク）")
        return results
