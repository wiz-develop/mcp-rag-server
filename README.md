# MCP RAG Server

MCP RAG Serverは、Model Context Protocol (MCP)に準拠したRAG（Retrieval-Augmented Generation）機能を持つPythonサーバーです。マークダウン、テキスト、パワーポイント、PDFなど複数の形式のドキュメントをデータソースとして、multilingual-e5-largeモデルを使用してインデックス化し、ベクトル検索によって関連情報を取得する機能を提供します。

## 概要

このプロジェクトは、MCPサーバーの基本的な実装に加えて、RAG機能を提供します。複数形式のドキュメントをインデックス化し、自然言語クエリに基づいて関連情報を検索することができます。

## 機能

- **MCPサーバーの基本実装**
  - JSON-RPC over stdioベースで動作（従来版）
  - **Streamable HTTP対応**（新機能：リモートMCPクライアント対応）
  - ツールの登録と実行のためのメカニズム
  - エラーハンドリングとロギング

- **RAG機能**
  - 複数形式のドキュメント（マークダウン、テキスト、パワーポイント、PDF）の読み込みと解析
  - 階層構造を持つソースディレクトリに対応
  - markitdownライブラリを使用したパワーポイントやPDFからのマークダウン変換
  - multilingual-e5-largeモデルを使用したエンベディング生成
  - PostgreSQLのpgvectorを使用したベクトルデータベース
  - ベクトル検索による関連情報の取得
  - 前後のチャンク取得機能（コンテキストの連続性を確保）
  - ドキュメント全文取得機能（完全なコンテキストを提供）
  - 差分インデックス化機能（新規・変更ファイルのみを処理）
  - **データマスキング機能**（機密情報の自動マスキング）

- **ツール**
  - ベクトル検索ツール（MCP）
  - ドキュメント数取得ツール（MCP）
  - インデックス管理ツール（CLI）

## 前提条件

- Python 3.10以上
- PostgreSQL 14以上（pgvectorエクステンション付き）

## インストール

### 依存関係のインストール

```bash
# uvがインストールされていない場合は先にインストール
# pip install uv

# 依存関係のインストール
uv sync
```

### PostgreSQLとpgvectorのセットアップ

#### Dockerを使用する場合

```bash
# pgvectorを含むPostgreSQLコンテナを起動
docker run --name postgres-pgvector -e POSTGRES_PASSWORD=password -p 5432:5432 -d pgvector/pgvector:pg14
```

#### データベースの作成

PostgreSQLコンテナを起動した後、以下のコマンドでデータベースを作成します：

```bash
# ragdbデータベースの作成
docker exec -it postgres-pgvector psql -U postgres -c "CREATE DATABASE ragdb;"
```

#### 既存のPostgreSQLにpgvectorをインストールする場合

```sql
-- pgvectorエクステンションをインストール
CREATE EXTENSION vector;
```

### 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定します：

```
# PostgreSQL接続情報
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=ragdb

# ドキュメントディレクトリ
SOURCE_DIR=./data/source
PROCESSED_DIR=./data/processed

# エンベディングモデル
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# データマスキング設定
MASKING_ENABLED=true
```

## 使い方

### MCPサーバーの起動

#### STDIO版（従来版：Claude Desktop等のローカル接続用）

uvを使用する場合（推奨）：

```bash
uv run python -m src.main
```

オプションを指定する場合：

```bash
uv run python -m src.main --name "my-rag-server" --version "1.0.0" --description "My RAG Server"
```

通常のPythonを使用する場合：

```bash
uv run python -m src.main
```

#### HTTP版（新機能：リモートMCP接続用）

Streamable HTTP MCPサーバーを起動する場合：

```bash
# デフォルト設定で起動（127.0.0.1:8000）
uv run python -m src.http_main

# ホストとポートを指定
uv run python -m src.http_main --host 0.0.0.0 --port 8080

# 全オプション指定
uv run python -m src.http_main --name "my-rag-server" --host 0.0.0.0 --port 8080 --path "/mcp" --log-level DEBUG
```

HTTP版のオプション：
- `--host`: サーバーのホスト（デフォルト: 127.0.0.1）
- `--port`: サーバーのポート（デフォルト: 8000）
- `--path`: MCPエンドポイントのパス（デフォルト: /mcp）
- `--log-level`: ログレベル（DEBUG, INFO, WARNING, ERROR）

HTTP版サーバーが起動すると、以下のURLでアクセス可能になります：
```
http://127.0.0.1:8000/mcp
```

#### Docker Compose（HTTP版の本格運用用）

HTTP版をDocker環境で実行する場合：

```bash
# PostgreSQLと一緒にHTTP MCPサーバーを起動
docker-compose -f docker-compose.http.yml up -d

# ログを確認
docker-compose -f docker-compose.http.yml logs -f mcp-rag-http-server

# 停止
docker-compose -f docker-compose.http.yml down
```

### コマンドラインツール（CLI）の使用方法

インデックスのクリアとインデックス化を行うためのコマンドラインツールが用意されています。

#### ヘルプの表示

```bash
uv run python -m src.cli --help
```

#### インデックスのクリア

```bash
uv run python -m src.cli clear
```

#### ドキュメントのインデックス化

```bash
# デフォルト設定でインデックス化（./data/source ディレクトリ）
uv run python -m src.cli index

# 特定のディレクトリをインデックス化
uv run python -m src.cli index --directory ./path/to/documents

# チャンクサイズとオーバーラップを指定してインデックス化
uv run python -m src.cli index --directory ./data/source --chunk-size 300 --chunk-overlap 50
# または短い形式で
uv run python -m src.cli index -d ./data/source -s 300 -o 50

# 差分インデックス化（新規・変更ファイルのみを処理）
uv run python -m src.cli index --incremental
# または短い形式で
uv run python -m src.cli index -i
```

#### インデックス内のドキュメント数の取得

```bash
uv run python -m src.cli count
```

### Cline/Cursorでの設定

Cline/CursorなどのAIツールでMCPサーバーを使用するには、`mcp_settings.json`ファイルに以下のような設定を追加します：

```json
"mcp-rag-server": {
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "/path/to/mcp-rag-server",
    "python",
    "-m",
    "src.main"
  ],
  "env": {},
  "disabled": false,
  "alwaysAllow": []
}
```

`/path/to/mcp-rag-server`は、このリポジトリのインストールディレクトリに置き換えてください。

## RAGツールの使用方法

### search

ベクトル検索を行います。

```json
{
  "jsonrpc": "2.0",
  "method": "search",
  "params": {
    "query": "Pythonのジェネレータとは何ですか？",
    "limit": 5,
    "with_context": true,
    "context_size": 1,
    "full_document": false
  },
  "id": 1
}
```

#### パラメータの説明

- `query`: 検索クエリ（必須）
- `limit`: 返す結果の数（デフォルト: 5）
- `with_context`: 前後のチャンクも取得するかどうか（デフォルト: true）
- `context_size`: 前後に取得するチャンク数（デフォルト: 1）
- `full_document`: ドキュメント全体を取得するかどうか（デフォルト: false）

#### 検索結果の改善

このツールは以下の機能により、より良い検索結果を提供します：

1. **前後のチャンク取得機能**：
   - 検索でヒットしたチャンクの前後のチャンクも取得して結果に含めます
   - `with_context`パラメータで有効/無効を切り替え可能
   - `context_size`パラメータで前後に取得するチャンク数を調整可能

2. **ドキュメント全文取得機能**：
   - 検索でヒットしたドキュメントの全文を取得して結果に含めます
   - `full_document`パラメータで有効/無効を切り替え可能
   - 特に短いドキュメントや全体の文脈が重要なドキュメントを扱う場合に有用

3. **結果の整形改善**：
   - 検索結果をファイルごとにグループ化
   - 「検索ヒット」「前後のコンテキスト」「ドキュメント全文」を視覚的に区別
   - チャンクインデックスでソートして文書の流れを維持

### get_document_count

インデックス内のドキュメント数を取得します。

```json
{
  "jsonrpc": "2.0",
  "method": "get_document_count",
  "params": {},
  "id": 2
}
```

## 使用例

1. ドキュメントファイルを `data/source` ディレクトリに配置します。サポートされるファイル形式は以下の通りです：
   - マークダウン（.md, .markdown）
   - テキスト（.txt）
   - パワーポイント（.ppt, .pptx）
   - Word（.doc, .docx）
   - PDF（.pdf）
   - Excel（.xls, .xlsx）
   - 画像（.jpg, .jpeg, .png）
   - HTML（.html）
   - Text-based formats（CSV, JSON, XML）
   - ZIP files (iterates over contents)

2. CLIコマンドを使用してドキュメントをインデックス化します：
   ```bash
   # 初回は全件インデックス化
   uv run python -m src.cli index

   # 以降は差分インデックス化で効率的に更新
   uv run python -m src.cli index -i
   ```

3. MCPサーバーを起動します：
   ```bash
   uv run python -m src.main
   ```

4. `search`ツールを使用して検索を行います。

## データマスキング機能

データマスキング機能は、ドキュメント処理時に機密情報を自動的に検出してマスキング（置換）する機能です。この機能により、ベクトルデータベースに機密情報が永続化されることを防ぐことができます。

### 機能概要

- **自動マスキング**: ファイル読み込み時に機密情報を自動検出・置換
- **カスタマイズ可能**: 環境変数でマスキングルールを柔軟に設定
- **デフォルトルール**: よくある機密情報パターンを事前定義

### デフォルトマスキングルール

データマスキング機能を有効にすると、以下の機密情報が自動的にマスキングされます：

| 対象 | 置換後 | 説明 |
|------|--------|------|
| メールアドレス | `[MASKED_EMAIL]` | test@example.com など |
| 電話番号（日本） | `[MASKED_PHONE]` | 03-1234-5678、090-1234-5678 など |
| クレジットカード番号 | `[MASKED_CREDIT_CARD]` | 1234-5678-9012-3456 など |
| マイナンバー | `[MASKED_SSN]` | 1234-56-789012 など |
| IPアドレス | `[MASKED_IP]` | 192.168.1.1 など |
| URL | `[MASKED_URL]` | https://example.com など |

### 設定方法

#### 基本設定

`.env`ファイルでマスキング機能を有効にします：

```env
# データマスキング機能を有効化
MASKING_ENABLED=true
```

#### カスタムマスキングルールの追加

環境変数でカスタムマスキングルールを定義できます：

```env
# 会社名のマスキング
MASK_RULE_COMPANY_PATTERN=株式会社[^\s]+
MASK_RULE_COMPANY_REPLACEMENT=[MASKED_COMPANY]
MASK_RULE_COMPANY_DESCRIPTION=会社名

# 従業員番号のマスキング
MASK_RULE_EMPLOYEE_PATTERN=EMP-\d{4,6}
MASK_RULE_EMPLOYEE_REPLACEMENT=[MASKED_EMPLOYEE_ID]
MASK_RULE_EMPLOYEE_DESCRIPTION=従業員番号

# 顧客IDのマスキング
MASK_RULE_CUSTOMER_PATTERN=CUST-[A-Z0-9]{8}
MASK_RULE_CUSTOMER_REPLACEMENT=[MASKED_CUSTOMER_ID]
MASK_RULE_CUSTOMER_DESCRIPTION=顧客ID
```

#### ルール定義の形式

カスタムマスキングルールは以下の形式で定義します：

```
MASK_RULE_<ルール名>_PATTERN=<正規表現パターン>
MASK_RULE_<ルール名>_REPLACEMENT=<置換文字列>
MASK_RULE_<ルール名>_DESCRIPTION=<ルールの説明>（オプション）
```

- **PATTERN**: マスキング対象を検出する正規表現
- **REPLACEMENT**: 検出された文字列を置換する文字列
- **DESCRIPTION**: ルールの説明（オプション、ログ出力に使用）

### 使用例

#### マスキング前のドキュメント
```markdown
# 顧客情報

- 氏名: 田中太郎
- メール: tanaka@company.com
- 電話: 03-1234-5678
- クレジットカード: 4111-1111-1111-1111
- ウェブサイト: https://company.com
```

#### マスキング後（MASKING_ENABLED=true）
```markdown
# 顧客情報

- 氏名: 田中太郎
- メール: [MASKED_EMAIL]
- 電話: [MASKED_PHONE]
- クレジットカード: [MASKED_CREDIT_CARD]
- ウェブサイト: [MASKED_URL]
```

### 動作タイミング

データマスキングは以下のタイミングで実行されます：

1. **ファイル読み込み時**: `DocumentProcessor.read_file()`
2. **マークダウン変換時**: Office文書・PDF変換後
3. **インデックス化前**: ベクトルデータベース格納前

これにより、機密情報がベクトルデータベースに永続化されることを防ぎます。

### 注意事項

- マスキング機能を有効にすると、検索時にも元の機密情報ではマッチしなくなります
- マスキングは不可逆的な処理です（元の情報に戻すことはできません）
- 正規表現パターンを慎重に設計して、必要な情報まで誤ってマスキングしないよう注意してください
- 大量のテキストを処理する場合、マスキング処理により若干の性能低下が発生する可能性があります

## バックアップと復元

インデックス化したデータベースを別のPCで使用するには、以下の手順でバックアップと復元を行います。

### 最小限のバックアップ（PostgreSQLデータベースのみ）

単純に他のPCでRAG検索機能を使いたいだけなら、PostgreSQLデータベースのバックアップだけで十分です。ベクトル化されたデータはすべてデータベースに保存されているためです。

#### PostgreSQLデータベースのバックアップ

PostgreSQLデータベースをバックアップするには、Dockerコンテナ内で`pg_dump`コマンドを使用します：

```bash
# Dockerコンテナ内でデータベースをバックアップ
docker exec -it postgres-pgvector pg_dump -U postgres -d ragdb -F c -f /tmp/ragdb_backup.dump

# バックアップファイルをコンテナからホストにコピー
docker cp postgres-pgvector:/tmp/ragdb_backup.dump ./ragdb_backup.dump
```

これにより、PostgreSQLデータベースのバックアップファイル（例：239MB）がカレントディレクトリに作成されます。

#### 最小限の復元手順

1. 新しいPCでPostgreSQLとpgvectorをセットアップします：

```bash
# Dockerを使用する場合
docker run --name postgres-pgvector -e POSTGRES_PASSWORD=password -p 5432:5432 -d pgvector/pgvector:pg14

# データベースを作成
docker exec -it postgres-pgvector psql -U postgres -c "CREATE DATABASE ragdb;"
```

2. バックアップからデータベースを復元します：

```bash
# バックアップファイルをコンテナにコピー
docker cp ./ragdb_backup.dump postgres-pgvector:/tmp/ragdb_backup.dump

# コンテナ内でデータベースを復元
docker exec -it postgres-pgvector pg_restore -U postgres -d ragdb -c /tmp/ragdb_backup.dump
```

3. 環境設定を確認します：

新しいPCでは、`.env`ファイルのPostgreSQL接続情報が正しく設定されていることを確認してください。

4. 動作確認：

```bash
python -m src.cli count
```

これにより、インデックス内のドキュメント数が表示されます。元のPCと同じ数が表示されれば、正常に復元されています。

### 完全バックアップ（オプション）

将来的に新しいドキュメントを追加する予定がある場合や、差分インデックス化機能を使用したい場合は、以下の追加バックアップも行うと良いでしょう：

#### 処理済みドキュメントのバックアップ

処理済みドキュメントディレクトリをバックアップします：

```bash
# 処理済みドキュメントディレクトリをZIPファイルにバックアップ
zip -r processed_data_backup.zip data/processed/
```

#### 環境設定ファイルのバックアップ

`.env`ファイルをバックアップします：

```bash
# .envファイルをコピー
cp .env env_backup.txt
```

#### 完全復元手順

1. 前提条件

新しいPCには以下のソフトウェアがインストールされている必要があります：

- Python 3.10以上
- PostgreSQL 14以上（pgvectorエクステンション付き）
- mcp-rag-serverのコードベース

2. PostgreSQLデータベースを上記の「最小限の復元手順」で復元します。

3. 処理済みドキュメントを復元します：

```bash
# ZIPファイルを展開
unzip processed_data_backup.zip -d /path/to/mcp-rag-server/
```

4. 環境設定ファイルを復元します：

```bash
# .envファイルを復元
cp env_backup.txt /path/to/mcp-rag-server/.env
```

必要に応じて、新しいPC環境に合わせて`.env`ファイルの設定（特にPostgreSQL接続情報）を編集します。

5. 動作確認：

```bash
python -m src.cli count
```

### 注意点

- PostgreSQLのバージョンとpgvectorのバージョンは、元のPCと新しいPCで互換性がある必要があります。
- 大量のデータがある場合は、バックアップと復元に時間がかかる場合があります。
- 新しいPCでは、必要なPythonパッケージ（`sentence-transformers`、`psycopg2-binary`など）をインストールしておく必要があります。

## ディレクトリ構造

```
mcp-rag-server/
├── data/
│   ├── source/        # 原稿ファイル（階層構造対応）
│   │   ├── markdown/  # マークダウンファイル
│   │   ├── docs/      # ドキュメントファイル
│   │   └── slides/    # プレゼンテーションファイル
│   └── processed/     # 処理済みファイル（テキスト抽出済み）
│       └── file_registry.json  # 処理済みファイルの情報（差分インデックス用）
├── docs/
│   └── design.md      # 設計書
├── logs/              # ログファイル
├── src/
│   ├── __init__.py
│   ├── document_processor.py  # ドキュメント処理モジュール
│   ├── embedding_generator.py # エンベディング生成モジュール
│   ├── example_tool.py        # サンプルツールモジュール
│   ├── main.py                # メインエントリーポイント
│   ├── mcp_server.py          # MCPサーバーモジュール
│   ├── rag_service.py         # RAGサービスモジュール
│   ├── rag_tools.py           # RAGツールモジュール
│   └── vector_database.py     # ベクトルデータベースモジュール
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_document_processor.py
│   ├── test_embedding_generator.py
│   ├── test_example_tool.py
│   ├── test_mcp_server.py
│   ├── test_rag_service.py
│   ├── test_rag_tools.py
│   └── test_vector_database.py
├── .env           # 環境変数設定ファイル
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
