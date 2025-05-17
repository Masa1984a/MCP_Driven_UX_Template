-- PostgreSQLデータベース初期化スクリプト
-- Firestoreモデルを元にしたRDBMSテーブル定義

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS mcp_ux;

-- 以降のテーブルはすべてmcp_uxスキーマに作成
SET search_path TO mcp_ux;

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(50) PRIMARY KEY,  -- Firestoreのドキュメントidに相当
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  role VARCHAR(50) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- アカウントテーブル
CREATE TABLE IF NOT EXISTS accounts (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- カテゴリテーブル
CREATE TABLE IF NOT EXISTS categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- カテゴリ詳細テーブル
CREATE TABLE IF NOT EXISTS category_details (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,  -- 非正規化だがFirestoreの構造を踏襲
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ステータステーブル
CREATE TABLE IF NOT EXISTS statuses (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 受付チャネルテーブル
CREATE TABLE IF NOT EXISTS request_channels (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 対応分類テーブル
CREATE TABLE IF NOT EXISTS response_categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_category VARCHAR(100),
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- チケット採番用シーケンス
CREATE SEQUENCE IF NOT EXISTS ticket_id_seq START 1;

-- チケットテーブル
CREATE TABLE IF NOT EXISTS tickets (
  id VARCHAR(50) PRIMARY KEY,  -- 形式は"TCK-XXXX"
  reception_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
  requestor_id VARCHAR(50) NOT NULL REFERENCES users(id),
  requestor_name VARCHAR(100) NOT NULL,  -- 非正規化
  account_id VARCHAR(50) NOT NULL REFERENCES accounts(id),
  account_name VARCHAR(100) NOT NULL,  -- 非正規化
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,  -- 非正規化
  category_detail_id VARCHAR(50) NOT NULL REFERENCES category_details(id),
  category_detail_name VARCHAR(200) NOT NULL,  -- 非正規化
  request_channel_id VARCHAR(50) NOT NULL REFERENCES request_channels(id),
  request_channel_name VARCHAR(50) NOT NULL,  -- 非正規化
  summary VARCHAR(200) NOT NULL,
  description TEXT,
  person_in_charge_id VARCHAR(50) NOT NULL REFERENCES users(id),
  person_in_charge_name VARCHAR(100) NOT NULL,  -- 非正規化
  status_id VARCHAR(50) NOT NULL REFERENCES statuses(id),
  status_name VARCHAR(50) NOT NULL,  -- 非正規化
  scheduled_completion_date DATE,
  completion_date DATE,
  actual_effort_hours NUMERIC(5,1),
  response_category_id VARCHAR(50) REFERENCES response_categories(id),
  response_category_name VARCHAR(100),  -- 非正規化
  response_details TEXT,
  has_defect BOOLEAN DEFAULT FALSE,
  external_ticket_id VARCHAR(50),
  remarks TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 添付ファイルテーブル
CREATE TABLE IF NOT EXISTS attachments (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  file_name VARCHAR(255) NOT NULL,
  file_url VARCHAR(1000) NOT NULL,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 対応履歴テーブル（チケットの変更履歴）
CREATE TABLE IF NOT EXISTS ticket_history (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  user_id VARCHAR(50) REFERENCES users(id),
  user_name VARCHAR(100) NOT NULL,  -- 非正規化
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 変更フィールド履歴テーブル（対応履歴の子テーブル）
CREATE TABLE IF NOT EXISTS history_changed_fields (
  id SERIAL PRIMARY KEY,
  history_id INTEGER NOT NULL REFERENCES ticket_history(id),
  field_name VARCHAR(100) NOT NULL,
  old_value TEXT,
  new_value TEXT
);

-- サンプルデータ - ユーザー
INSERT INTO users (id, name, email, role) VALUES
  ('user1', '山田 太郎', 'taro.yamada@example.com', '担当者'),
  ('user2', '鈴木 花子', 'hanako.suzuki@example.com', '担当者'),
  ('user3', '佐藤 次郎', 'jiro.sato@example.com', 'リクエスタ'),
  ('user4', '高橋 三郎', 'saburo.takahashi@example.com', 'リクエスタ');

-- サンプルデータ - アカウント
INSERT INTO accounts (id, name, order_no) VALUES
  ('acc1', '株式会社ABC', 1),
  ('acc2', 'XYZ株式会社', 2),
  ('acc3', '123株式会社', 3);

-- サンプルデータ - カテゴリ
INSERT INTO categories (id, name, order_no) VALUES
  ('cat1', '問合せ', 1),
  ('cat2', 'データ修正依頼', 2),
  ('cat3', '障害報告', 3);

-- サンプルデータ - カテゴリ詳細
INSERT INTO category_details (id, name, category_id, category_name, order_no) VALUES
  ('catd1', 'ポータル・記事・検索機能に関する問合せ', 'cat1', '問合せ', 1),
  ('catd2', 'サポート管理に関する問合せ', 'cat1', '問合せ', 2),
  ('catd3', 'マスターデータ修正依頼', 'cat2', 'データ修正依頼', 1),
  ('catd4', 'システム障害', 'cat3', '障害報告', 1);

-- サンプルデータ - ステータス
INSERT INTO statuses (id, name, order_no) VALUES
  ('stat1', '受付済', 1),
  ('stat2', '対応中', 2),
  ('stat3', '確認中', 3),
  ('stat4', '完了', 4);

-- サンプルデータ - 受付チャネル
INSERT INTO request_channels (id, name, order_no) VALUES
  ('ch1', 'Email', 1),
  ('ch2', '電話', 2),
  ('ch3', 'Teams', 3);

-- サンプルデータ - 対応分類
INSERT INTO response_categories (id, name, parent_category, order_no) VALUES
  ('resp1', 'Japanから回答可', '問合せ', 1),
  ('resp2', '無償対応', 'データ修正依頼', 1),
  ('resp3', '開発修正対応', '障害報告', 1);

-- サンプルデータ - チケット 1
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0001',
  NOW() - INTERVAL '5 days',
  'user3', '佐藤 次郎',
  'acc1', '株式会社ABC',
  'cat1', '問合せ',
  'catd1', 'ポータル・記事・検索機能に関する問合せ',
  'ch1', 'Email',
  '検索機能が正常に動作しない',
  '検索ボックスに特定のキーワードを入力しても結果が表示されません。\n再現手順：\n1. トップページの検索ボックスに「特殊文字」を含む検索語を入力\n2. 検索ボタンをクリック\n3. 「検索結果がありません」と表示される',
  'user1', '山田 太郎',
  'stat2', '対応中',
  CURRENT_DATE + INTERVAL '2 days',
  FALSE,
  'EXT-123'
);

-- チケット1の添付ファイル
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0001', 'error_screenshot.png', 'https://example.com/storage/error_screenshot.png', NOW() - INTERVAL '5 days');

-- チケット1の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '5 days', 'user1', '山田 太郎', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '3 days', 'user1', '山田 太郎', '調査を開始しました。特殊文字のエスケープ処理に問題がある可能性があります。');

-- チケット1の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (2, 'status', '受付済', '対応中');

-- サンプルデータ - チケット 2
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect
) VALUES (
  'TCK-0002',
  NOW() - INTERVAL '10 days',
  'user4', '高橋 三郎',
  'acc2', 'XYZ株式会社',
  'cat2', 'データ修正依頼',
  'catd3', 'マスターデータ修正依頼',
  'ch2', '電話',
  'ユーザーマスターの情報更新依頼',
  '弊社の担当者が変更になりました。以下の通り更新をお願いします。\n\n旧担当：鈴木一郎\n新担当：田中五郎\nメールアドレス：goro.tanaka@xyz.co.jp\n電話番号：03-1234-5678',
  'user2', '鈴木 花子',
  'stat4', '完了',
  CURRENT_DATE - INTERVAL '8 days',
  CURRENT_DATE - INTERVAL '9 days',
  1.5,
  'resp2', '無償対応',
  'マスターデータの更新が完了しました。\n変更内容の確認をお願いします。',
  FALSE
);

-- チケット2の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '10 days', 'user2', '鈴木 花子', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '9 days', 'user2', '鈴木 花子', 'マスターデータの更新が完了しました。お客様に確認依頼のメールを送信しました。');

-- チケット2の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (4, 'status', '受付済', '完了');

-- サンプルチケット3
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0003',
  NOW() - INTERVAL '1 day',
  'user3', '佐藤 次郎',
  'acc1', '株式会社ABC',
  'cat3', '障害報告',
  'catd4', 'システム障害',
  'ch3', 'Teams',
  'ダッシュボードが表示されない',
  '今朝からダッシュボードにアクセスするとエラーが表示されます。\nエラーメッセージ：「データの読み込みに失敗しました」\n\n複数のユーザーで同様の事象が発生しています。',
  'user1', '山田 太郎',
  'stat1', '受付済',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'INC-456',
  '緊急対応が必要です。'
);

-- チケット3の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0003', NOW() - INTERVAL '1 day', 'user1', '山田 太郎', '新規チケット作成');

-- 次回のチケットID用にシーケンスの値を更新
SELECT setval('ticket_id_seq', 3, true);