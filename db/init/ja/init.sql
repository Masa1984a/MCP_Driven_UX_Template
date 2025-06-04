-- PostgreSQLデータベース初期化スクリプト

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS mcp_ux;

-- 以降のテーブルはすべてmcp_uxスキーマに作成
SET search_path TO mcp_ux;

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(50) PRIMARY KEY,
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
  category_name VARCHAR(100) NOT NULL,
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
  ('user4', '高橋 三郎', 'saburo.takahashi@example.com', 'リクエスタ'),
  ('user5', '上司 進', 'susumu.joshi@example.com', '管理者'),
  ('user6', '田中 美咲', 'misaki.tanaka@example.com', '担当者'),
  ('user7', '伊藤 健一', 'kenichi.ito@example.com', 'リクエスタ'),
  ('user8', '渡辺 さくら', 'sakura.watanabe@example.com', 'リクエスタ');

-- サンプルデータ - アカウント
INSERT INTO accounts (id, name, order_no) VALUES
  ('acc1', '株式会社ABC', 1),
  ('acc2', 'XYZ株式会社', 2),
  ('acc3', '123株式会社', 3),
  ('acc4', 'グローバルテック株式会社', 4),
  ('acc5', 'イノベーションラボ株式会社', 5);

-- サンプルデータ - カテゴリ
INSERT INTO categories (id, name, order_no) VALUES
  ('cat1', '問合せ', 1),
  ('cat2', 'データ修正依頼', 2),
  ('cat3', '障害報告', 3),
  ('cat4', 'UX改修依頼', 4),
  ('cat5', '機能追加依頼', 5);

-- サンプルデータ - カテゴリ詳細
INSERT INTO category_details (id, name, category_id, category_name, order_no) VALUES
  ('catd1', 'ポータル・記事・検索機能に関する問合せ', 'cat1', '問合せ', 1),
  ('catd2', 'サポート管理に関する問合せ', 'cat1', '問合せ', 2),
  ('catd3', 'マスターデータ修正依頼', 'cat2', 'データ修正依頼', 1),
  ('catd4', 'システム障害', 'cat3', '障害報告', 1),
  ('catd5', 'UI/UX改善提案', 'cat4', 'UX改修依頼', 1),
  ('catd6', '検索機能改善提案', 'cat4', 'UX改修依頼', 2),
  ('catd7', '新機能開発', 'cat5', '機能追加依頼', 1),
  ('catd8', '連携機能追加', 'cat5', '機能追加依頼', 2);

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
  ('ch3', 'Teams', 3),
  ('ch4', 'Chat/LLM', 4),
  ('ch5', 'Webフォーム', 5);

-- サンプルデータ - 対応分類
INSERT INTO response_categories (id, name, parent_category, order_no) VALUES
  ('resp1', 'Japanから回答可', '問合せ', 1),
  ('resp2', '無償対応', 'データ修正依頼', 1),
  ('resp3', '開発修正対応', '障害報告', 1),
  ('resp4', 'デザイン検討必要', 'UX改修依頼', 1),
  ('resp5', '実装予定', '機能追加依頼', 1);

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

-- サンプルデータ - チケット 4 (検索関連の問題)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0004',
  NOW() - INTERVAL '2 days',
  'user7', '伊藤 健一',
  'acc4', 'グローバルテック株式会社',
  'cat1', '問合せ',
  'catd1', 'ポータル・記事・検索機能に関する問合せ',
  'ch4', 'Chat/LLM',
  '全文検索が一部ヒットしない',
  '全文検索機能を使用した際に、特定のキーワードが含まれているはずの記事がヒットしません。\n再現手順：\n1. 検索ボックスに「運用マニュアル」と入力\n2. 検索ボタンをクリック\n3. 「運用マニュアル」という単語を含む記事が検索結果に表示されない',
  'user6', '田中 美咲',
  'stat2', '対応中',
  CURRENT_DATE + INTERVAL '5 days',
  TRUE,
  'BUG-789'
);

-- チケット4の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '2 days', 'user6', '田中 美咲', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '1 day', 'user6', '田中 美咲', '調査を開始しました。特殊文字のインデックス処理に問題があることがわかりました。');

-- チケット4の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (6, 'status', '受付済', '対応中');

-- サンプルデータ - チケット 5 (UX改善)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0005',
  NOW() - INTERVAL '7 days',
  'user8', '渡辺 さくら',
  'acc5', 'イノベーションラボ株式会社',
  'cat4', 'UX改修依頼',
  'catd6', '検索機能改善提案',
  'ch1', 'Email',
  '検索結果の並び順をカスタマイズしたい',
  '検索結果が現在は日付順に表示されていますが、関連度順やカテゴリ別などでの並べ替えができるようにしたいです。\nユーザーからのフィードバックとして「探しているものが見つけづらい」という声があります。',
  'user1', '山田 太郎',
  'stat3', '確認中',
  CURRENT_DATE + INTERVAL '14 days',
  FALSE
);

-- チケット5の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '7 days', 'user1', '山田 太郎', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '5 days', 'user1', '山田 太郎', '提案内容を確認しました。新しい並び替えオプションのモックアップを作成中です。');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '2 days', 'user1', '山田 太郎', 'モックアップを依頼者に送付し、レビューを依頼しました。');

-- チケット5の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (8, 'status', '受付済', '対応中');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (9, 'status', '対応中', '確認中');

-- サンプルデータ - チケット 6 (パフォーマンス問題)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0006',
  NOW() - INTERVAL '3 days',
  'user3', '佐藤 次郎',
  'acc1', '株式会社ABC',
  'cat3', '障害報告',
  'catd4', 'システム障害',
  'ch3', 'Teams',
  '検索機能のパフォーマンスが低下',
  '先週のアップデート以降、検索機能の応答速度が著しく低下しています。\n特に大量の検索結果が返される場合に10秒以上かかることがあります。\nAPMツールのログも添付します。',
  'user2', '鈴木 花子',
  'stat2', '対応中',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'PERF-456',
  '優先度高 - 複数のユーザーに影響'
);

-- チケット6の添付ファイル
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0006', 'apm_logs.txt', 'https://example.com/storage/apm_logs.txt', NOW() - INTERVAL '3 days'),
  ('TCK-0006', 'performance_metrics.pdf', 'https://example.com/storage/performance_metrics.pdf', NOW() - INTERVAL '3 days');

-- チケット6の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '3 days', 'user2', '鈴木 花子', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '2 days', 'user2', '鈴木 花子', 'パフォーマンス分析を開始しました。データベースクエリの最適化が必要であることが判明しました。');

-- チケット6の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (12, 'status', '受付済', '対応中');

-- サンプルデータ - チケット 7 (機能追加依頼)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect
) VALUES (
  'TCK-0007',
  NOW() - INTERVAL '15 days',
  'user4', '高橋 三郎',
  'acc2', 'XYZ株式会社',
  'cat5', '機能追加依頼',
  'catd7', '新機能開発',
  'ch5', 'Webフォーム',
  '高度な検索フィルター機能の実装',
  '以下のフィルターを使用した高度な検索機能を希望します：\n- 日付範囲\n- ドキュメントタイプ\n- タグ/カテゴリ\n- 作成者\n- ステータス\nこれにより、特定のドキュメントを迅速に見つける能力が大幅に向上します。',
  'user1', '山田 太郎',
  'stat4', '完了',
  CURRENT_DATE - INTERVAL '10 days',
  CURRENT_DATE - INTERVAL '2 days',
  24.5,
  'resp5', '実装予定',
  '高度な検索フィルター機能を実装し、本番環境にデプロイしました。ユーザーは複数の条件で検索結果をフィルタリングできるようになりました。',
  FALSE
);

-- チケット7の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '15 days', 'user1', '山田 太郎', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '12 days', 'user1', '山田 太郎', '開発を開始しました。UIモックアップとバックエンドAPIの設計を作成しました。');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '2 days', 'user1', '山田 太郎', '機能の実装が完了し、本番環境にデプロイしました。');

-- チケット7の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (14, 'status', '受付済', '対応中');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (15, 'status', '対応中', '完了');

-- サンプルデータ - チケット 8 (連携機能追加)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0008',
  NOW() - INTERVAL '4 days',
  'user7', '伊藤 健一',
  'acc4', 'グローバルテック株式会社',
  'cat5', '機能追加依頼',
  'catd8', '連携機能追加',
  'ch2', '電話',
  '通知用のSlack API連携',
  '以下のタイミングでSlackにリアルタイム通知を受け取れるよう、チケットシステムとの連携を希望します：\n- 新規チケット作成時\n- チケットがチームメンバーに割り当てられた時\n- ステータス変更時\n- コメント追加時\nこれにより、応答時間が大幅に改善されます。',
  'user6', '田中 美咲',
  'stat1', '受付済',
  CURRENT_DATE + INTERVAL '21 days',
  FALSE
);

-- チケット8の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0008', NOW() - INTERVAL '4 days', 'user6', '田中 美咲', '新規チケット作成');

-- サンプルデータ - チケット 9 (ログイン問題)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0009',
  NOW() - INTERVAL '6 days',
  'user4', '高橋 三郎',
  'acc3', '123株式会社',
  'cat1', '問合せ',
  'catd2', 'サポート管理に関する問合せ',
  'ch1', 'Email',
  'ログイン機能に関する問題',
  'パスワードを忘れた場合のリセット方法について問い合わせがありました。具体的には、パスワードリセットメールが届かないという点について詳細を確認したいとのことです。',
  'user2', '鈴木 花子',
  'stat3', '確認中',
  CURRENT_DATE + INTERVAL '4 days',
  FALSE
);

-- チケット9の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0009', NOW() - INTERVAL '6 days', 'user2', '鈴木 花子', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0009', NOW() - INTERVAL '4 days', 'user2', '鈴木 花子', 'メールサーバーの設定を確認中です。');

-- チケット9の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (17, 'status', '受付済', '確認中');

-- サンプルデータ - チケット 10 (ダッシュボード改善)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0010',
  NOW() - INTERVAL '8 days',
  'user8', '渡辺 さくら',
  'acc5', 'イノベーションラボ株式会社',
  'cat4', 'UX改修依頼',
  'catd5', 'UI/UX改善提案',
  'ch3', 'Teams',
  'ダッシュボードのグラフ表示期間設定',
  'ダッシュボードに関する問題が報告されています。症状としては、表示されるグラフの期間設定方法という現象が発生しています。',
  'user1', '山田 太郎',
  'stat2', '対応中',
  CURRENT_DATE + INTERVAL '7 days',
  FALSE
);

-- チケット10の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0010', NOW() - INTERVAL '8 days', 'user1', '山田 太郎', '新規チケット作成');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0010', NOW() - INTERVAL '6 days', 'user1', '山田 太郎', '期間選択UIの改善案を検討中です。');

-- チケット10の履歴の変更フィールド
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (19, 'status', '受付済', '対応中');

-- サンプルデータ - チケット 11-20
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect
) VALUES 
('TCK-0011', NOW() - INTERVAL '12 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat2', 'データ修正依頼', 'catd3', 'マスターデータ修正依頼', 'ch2', '電話',
 'ユーザー管理のアカウント情報更新', 'ユーザー管理に関する情報を更新してほしいとの依頼がありました。具体的にはアカウント情報の一括更新方法の部分を修正する必要があります。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE - INTERVAL '11 days', 2.5,
 'resp2', '無償対応', 'アカウント情報の更新が完了しました。', FALSE),

('TCK-0012', NOW() - INTERVAL '9 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch4', 'Chat/LLM',
 'レポート機能の不具合', 'レポート機能の使用中に問題が発生したとの報告がありました。カスタムレポートの作成手順の状況で再現するようです。',
 'user2', '鈴木 花子', 'stat2', '対応中', CURRENT_DATE + INTERVAL '3 days', NULL, NULL,
 NULL, NULL, NULL, TRUE),

('TCK-0013', NOW() - INTERVAL '11 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch1', 'Email',
 'データエクスポート機能について', 'ユーザーからデータエクスポートについて問い合わせがありました。具体的には、CSVダウンロード時のエンコード設定という点について詳細を確認したいとのことです。',
 'user1', '山田 太郎', 'stat3', '確認中', CURRENT_DATE + INTERVAL '5 days', NULL, NULL,
 NULL, NULL, NULL, FALSE),

('TCK-0014', NOW() - INTERVAL '14 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat5', '機能追加依頼', 'catd8', '連携機能追加', 'ch5', 'Webフォーム',
 'API連携の実装依頼', 'API連携機能について改善リクエストがあります。現状ではサードパーティツールとの連携手順ですが、これを改善してほしいとの要望です。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE - INTERVAL '8 days', 16.0,
 'resp5', '実装予定', 'API連携機能を実装し、ドキュメントも更新しました。', FALSE),

('TCK-0015', NOW() - INTERVAL '5 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat1', '問合せ', 'catd2', 'サポート管理に関する問合せ', 'ch3', 'Teams',
 'アクセス権限の設定方法', 'アクセス権限に関する問題が報告されています。症状としては、特定ページへのアクセス制限設定という現象が発生しています。',
 'user2', '鈴木 花子', 'stat1', '受付済', CURRENT_DATE + INTERVAL '10 days', NULL, NULL,
 NULL, NULL, NULL, FALSE),

('TCK-0016', NOW() - INTERVAL '13 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat2', 'データ修正依頼', 'catd3', 'マスターデータ修正依頼', 'ch2', '電話',
 '通知設定の変更依頼', '通知設定に関する情報を更新してほしいとの依頼がありました。具体的にはメール通知の頻度変更方法の部分を修正する必要があります。',
 'user1', '山田 太郎', 'stat4', '完了', CURRENT_DATE - INTERVAL '11 days', CURRENT_DATE - INTERVAL '12 days', 1.0,
 'resp2', '無償対応', '通知設定の変更が完了しました。', FALSE),

('TCK-0017', NOW() - INTERVAL '4 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch1', 'Email',
 'セキュリティ設定のエラー', 'セキュリティ設定の使用中に問題が発生したとの報告がありました。二段階認証の有効化方法の状況で再現するようです。',
 'user6', '田中 美咲', 'stat2', '対応中', CURRENT_DATE + INTERVAL '2 days', NULL, NULL,
 NULL, NULL, NULL, TRUE),

('TCK-0018', NOW() - INTERVAL '16 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat4', 'UX改修依頼', 'catd5', 'UI/UX改善提案', 'ch4', 'Chat/LLM',
 'モバイル対応の改善要望', 'モバイル対応機能について改善リクエストがあります。現状ではスマートフォン表示時のレイアウト崩れですが、これを改善してほしいとの要望です。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '14 days', CURRENT_DATE - INTERVAL '15 days', 8.5,
 'resp4', 'デザイン検討必要', 'レスポンシブデザインを実装し、モバイル表示を最適化しました。', FALSE),

('TCK-0019', NOW() - INTERVAL '7 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch2', '電話',
 '検索結果のフィルタリング', 'ユーザーから検索機能について問い合わせがありました。具体的には、検索結果の絞り込み機能という点について詳細を確認したいとのことです。',
 'user1', '山田 太郎', 'stat2', '対応中', CURRENT_DATE + INTERVAL '6 days', NULL, NULL,
 NULL, NULL, NULL, FALSE),

('TCK-0020', NOW() - INTERVAL '10 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat5', '機能追加依頼', 'catd7', '新機能開発', 'ch5', 'Webフォーム',
 'バッチ処理機能の追加', 'データの一括処理機能について改善リクエストがあります。現状では手動での個別処理ですが、これを自動化してほしいとの要望です。',
 'user6', '田中 美咲', 'stat3', '確認中', CURRENT_DATE + INTERVAL '15 days', NULL, NULL,
 NULL, NULL, NULL, FALSE);

-- チケット11-20の履歴エントリー
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0011', NOW() - INTERVAL '12 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0012', NOW() - INTERVAL '9 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0013', NOW() - INTERVAL '11 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0014', NOW() - INTERVAL '14 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0015', NOW() - INTERVAL '5 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0016', NOW() - INTERVAL '13 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0017', NOW() - INTERVAL '4 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0018', NOW() - INTERVAL '16 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0019', NOW() - INTERVAL '7 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0020', NOW() - INTERVAL '10 days', 'user6', '田中 美咲', '新規チケット作成');

-- サンプルデータ - チケット 21-30
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES 
('TCK-0021', NOW() - INTERVAL '18 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat1', '問合せ', 'catd2', 'サポート管理に関する問合せ', 'ch1', 'Email',
 '権限管理システムについて', 'ユーザー権限の一括変更方法について問い合わせがありました。複数ユーザーの権限を効率的に管理したいとのことです。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '16 days', FALSE, 'SUP-1021'),

('TCK-0022', NOW() - INTERVAL '3 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch3', 'Teams',
 'ファイルアップロード機能の不具合', '大容量ファイルのアップロード時にタイムアウトエラーが発生します。10MB以上のファイルで必ず発生する状況です。',
 'user1', '山田 太郎', 'stat2', '対応中', CURRENT_DATE + INTERVAL '4 days', TRUE, 'BUG-2022'),

('TCK-0023', NOW() - INTERVAL '20 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat4', 'UX改修依頼', 'catd6', '検索機能改善提案', 'ch4', 'Chat/LLM',
 '検索履歴の保存機能', '検索履歴を保存して、よく使う検索条件を簡単に再利用できるようにしてほしいです。業務効率化につながります。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '18 days', FALSE, NULL),

('TCK-0024', NOW() - INTERVAL '15 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat2', 'データ修正依頼', 'catd3', 'マスターデータ修正依頼', 'ch2', '電話',
 '部署情報の一括更新', '組織改編に伴い、部署マスターの大量更新が必要です。約200件の部署情報を更新する必要があります。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '13 days', FALSE, NULL),

('TCK-0025', NOW() - INTERVAL '6 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat5', '機能追加依頼', 'catd8', '連携機能追加', 'ch5', 'Webフォーム',
 'Microsoft Teams連携', 'チケットの更新情報をMicrosoft Teamsのチャネルに自動投稿する機能を追加してほしいです。',
 'user1', '山田 太郎', 'stat3', '確認中', CURRENT_DATE + INTERVAL '20 days', FALSE, 'REQ-2025'),

('TCK-0026', NOW() - INTERVAL '22 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch1', 'Email',
 '検索結果のエクスポート', '検索結果をExcelファイルにエクスポートする方法について教えてください。月次レポート作成に必要です。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '20 days', FALSE, NULL),

('TCK-0027', NOW() - INTERVAL '8 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch3', 'Teams',
 'ログイン後の画面遷移エラー', '特定のユーザーでログイン後、ダッシュボードに遷移せず白い画面が表示される問題が発生しています。',
 'user2', '鈴木 花子', 'stat2', '対応中', CURRENT_DATE + INTERVAL '3 days', TRUE, 'INC-2027'),

('TCK-0028', NOW() - INTERVAL '19 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat4', 'UX改修依頼', 'catd5', 'UI/UX改善提案', 'ch2', '電話',
 'ダークモードの実装', 'UIにダークモードを追加してほしいです。長時間作業する際の目の疲れを軽減したいです。',
 'user1', '山田 太郎', 'stat4', '完了', CURRENT_DATE - INTERVAL '17 days', FALSE, NULL),

('TCK-0029', NOW() - INTERVAL '5 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat1', '問合せ', 'catd2', 'サポート管理に関する問合せ', 'ch4', 'Chat/LLM',
 '自動バックアップ設定について', 'システムの自動バックアップ設定方法と、リストア手順について確認したいです。',
 'user6', '田中 美咲', 'stat1', '受付済', CURRENT_DATE + INTERVAL '8 days', FALSE, NULL),

('TCK-0030', NOW() - INTERVAL '21 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat5', '機能追加依頼', 'catd7', '新機能開発', 'ch5', 'Webフォーム',
 'AIによる自動分類機能', 'チケット作成時にAIが内容を分析して、自動的にカテゴリを提案する機能を追加してほしいです。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '19 days', FALSE, 'AI-2030');

-- チケット21-30の添付ファイル
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0022', 'error_log_upload.txt', 'https://example.com/storage/TCK-0022/error_log_upload.txt', NOW() - INTERVAL '3 days'),
  ('TCK-0024', 'department_update_list.xlsx', 'https://example.com/storage/TCK-0024/department_update_list.xlsx', NOW() - INTERVAL '15 days'),
  ('TCK-0027', 'login_error_screenshot.png', 'https://example.com/storage/TCK-0027/login_error_screenshot.png', NOW() - INTERVAL '8 days');

-- チケット21-30の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0021', NOW() - INTERVAL '18 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0021', NOW() - INTERVAL '17 days', 'user2', '鈴木 花子', '権限管理のマニュアルを提供し、解決しました。'),
  ('TCK-0022', NOW() - INTERVAL '3 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0023', NOW() - INTERVAL '20 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0024', NOW() - INTERVAL '15 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0025', NOW() - INTERVAL '6 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0026', NOW() - INTERVAL '22 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0027', NOW() - INTERVAL '8 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0028', NOW() - INTERVAL '19 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0029', NOW() - INTERVAL '5 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0030', NOW() - INTERVAL '21 days', 'user2', '鈴木 花子', '新規チケット作成');

-- サンプルデータ - チケット 31-40
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, remarks
) VALUES 
('TCK-0031', NOW() - INTERVAL '9 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch2', '電話',
 '検索APIの利用方法', '外部システムから検索APIを利用したいのですが、APIドキュメントの場所と認証方法について教えてください。',
 'user1', '山田 太郎', 'stat2', '対応中', CURRENT_DATE + INTERVAL '5 days', FALSE, 'API連携プロジェクトの一環'),

('TCK-0032', NOW() - INTERVAL '24 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch1', 'Email',
 'メモリリークの疑い', '長時間運用していると、システムのメモリ使用量が徐々に増加し、最終的にシステムが不安定になります。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '22 days', TRUE, '修正パッチ適用済み'),

('TCK-0033', NOW() - INTERVAL '11 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat4', 'UX改修依頼', 'catd6', '検索機能改善提案', 'ch3', 'Teams',
 '検索サジェスト機能', '検索ボックスに文字を入力した際に、過去の検索履歴や人気の検索キーワードをサジェストする機能が欲しいです。',
 'user2', '鈴木 花子', 'stat3', '確認中', CURRENT_DATE + INTERVAL '10 days', FALSE, 'ユーザビリティ向上施策'),

('TCK-0034', NOW() - INTERVAL '17 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat2', 'データ修正依頼', 'catd3', 'マスターデータ修正依頼', 'ch4', 'Chat/LLM',
 'カテゴリマスターの追加', '新しい業務に対応するため、カテゴリマスターに5つの新規カテゴリを追加してください。',
 'user1', '山田 太郎', 'stat4', '完了', CURRENT_DATE - INTERVAL '15 days', FALSE, NULL),

('TCK-0035', NOW() - INTERVAL '7 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat5', '機能追加依頼', 'catd8', '連携機能追加', 'ch5', 'Webフォーム',
 'Webhookによるイベント通知', 'チケットのステータス変更時に、指定したURLにWebhookで通知を送る機能を実装してください。',
 'user6', '田中 美咲', 'stat2', '対応中', CURRENT_DATE + INTERVAL '14 days', FALSE, '開発環境で検証中'),

('TCK-0036', NOW() - INTERVAL '23 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat1', '問合せ', 'catd2', 'サポート管理に関する問合せ', 'ch1', 'Email',
 'SLA設定について', 'チケットの種類ごとにSLA（サービスレベルアグリーメント）を設定する方法を教えてください。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '21 days', FALSE, NULL),

('TCK-0037', NOW() - INTERVAL '4 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch2', '電話',
 '印刷機能の不具合', 'チケット詳細画面から印刷を実行すると、レイアウトが崩れて正しく印刷されません。',
 'user1', '山田 太郎', 'stat2', '対応中', CURRENT_DATE + INTERVAL '3 days', TRUE, '印刷用CSSの調整が必要'),

('TCK-0038', NOW() - INTERVAL '25 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat4', 'UX改修依頼', 'catd5', 'UI/UX改善提案', 'ch3', 'Teams',
 'キーボードショートカット', '効率的な操作のため、よく使う機能にキーボードショートカットを割り当ててほしいです。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '23 days', FALSE, NULL),

('TCK-0039', NOW() - INTERVAL '12 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch4', 'Chat/LLM',
 '全文検索の対象範囲', '全文検索で検索される対象（タイトル、本文、コメント等）について詳しく教えてください。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '10 days', FALSE, NULL),

('TCK-0040', NOW() - INTERVAL '16 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat5', '機能追加依頼', 'catd7', '新機能開発', 'ch5', 'Webフォーム',
 'カンバンビューの追加', 'チケットをカンバン形式で表示・管理できるビューを追加してください。ドラッグ&ドロップでステータス変更もできると嬉しいです。',
 'user1', '山田 太郎', 'stat3', '確認中', CURRENT_DATE + INTERVAL '25 days', FALSE, '要件定義中');

-- チケット31-40の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0031', NOW() - INTERVAL '9 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0032', NOW() - INTERVAL '24 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0033', NOW() - INTERVAL '11 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0034', NOW() - INTERVAL '17 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0035', NOW() - INTERVAL '7 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0036', NOW() - INTERVAL '23 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0037', NOW() - INTERVAL '4 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0038', NOW() - INTERVAL '25 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0039', NOW() - INTERVAL '12 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0040', NOW() - INTERVAL '16 days', 'user1', '山田 太郎', '新規チケット作成');

-- サンプルデータ - チケット 41-50
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, completion_date, actual_effort_hours,
  response_category_id, response_category_name, response_details, has_defect, external_ticket_id
) VALUES 
('TCK-0041', NOW() - INTERVAL '26 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch1', 'Email',
 '検索インデックスの破損', '特定の日付以降に登録されたデータが検索結果に表示されない問題が発生しています。インデックスの再構築が必要かもしれません。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '24 days', CURRENT_DATE - INTERVAL '25 days', 12.0,
 'resp3', '開発修正対応', 'インデックスを再構築し、問題を解決しました。', TRUE, 'SRCH-4041'),

('TCK-0042', NOW() - INTERVAL '13 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat1', '問合せ', 'catd2', 'サポート管理に関する問合せ', 'ch3', 'Teams',
 'レポート機能のカスタマイズ', 'デフォルトのレポートテンプレートをカスタマイズする方法について教えてください。',
 'user6', '田中 美咲', 'stat4', '完了', CURRENT_DATE - INTERVAL '11 days', CURRENT_DATE - INTERVAL '12 days', 3.0,
 'resp1', 'Japanから回答可', 'カスタマイズ手順書を提供しました。', FALSE, NULL),

('TCK-0043', NOW() - INTERVAL '2 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat4', 'UX改修依頼', 'catd6', '検索機能改善提案', 'ch4', 'Chat/LLM',
 '検索結果のハイライト表示', '検索結果で、検索キーワードに該当する部分をハイライト表示してほしいです。どこがマッチしたか分かりやすくなります。',
 'user1', '山田 太郎', 'stat1', '受付済', CURRENT_DATE + INTERVAL '12 days', NULL, NULL,
 NULL, NULL, NULL, FALSE, 'UI-4043'),

('TCK-0044', NOW() - INTERVAL '28 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat2', 'データ修正依頼', 'catd3', 'マスターデータ修正依頼', 'ch2', '電話',
 'ユーザー権限の一括変更', '人事異動に伴い、50名分のユーザー権限を一括で変更する必要があります。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '26 days', CURRENT_DATE - INTERVAL '27 days', 4.5,
 'resp2', '無償対応', '権限変更スクリプトを作成し、一括更新を完了しました。', FALSE, NULL),

('TCK-0045', NOW() - INTERVAL '14 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat5', '機能追加依頼', 'catd8', '連携機能追加', 'ch5', 'Webフォーム',
 'Google Calendar連携', 'チケットの期限をGoogle Calendarに自動的に登録する機能を追加してください。',
 'user6', '田中 美咲', 'stat2', '対応中', CURRENT_DATE + INTERVAL '18 days', NULL, NULL,
 NULL, NULL, NULL, FALSE, 'INT-4045'),

('TCK-0046', NOW() - INTERVAL '1 day', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch1', 'Email',
 'CSVインポートエラー', 'CSVファイルでデータをインポートしようとすると、文字化けが発生します。UTF-8でエンコードしても改善しません。',
 'user1', '山田 太郎', 'stat2', '対応中', CURRENT_DATE + INTERVAL '2 days', NULL, NULL,
 NULL, NULL, NULL, TRUE, 'CSV-4046'),

('TCK-0047', NOW() - INTERVAL '27 days', 'user3', '佐藤 次郎', 'acc1', '株式会社ABC',
 'cat1', '問合せ', 'catd1', 'ポータル・記事・検索機能に関する問合せ', 'ch3', 'Teams',
 '検索パフォーマンスの最適化', '検索処理が遅い場合の最適化方法について、ベストプラクティスを教えてください。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE - INTERVAL '26 days', 2.0,
 'resp1', 'Japanから回答可', 'パフォーマンスチューニングガイドを提供しました。', FALSE, NULL),

('TCK-0048', NOW() - INTERVAL '10 days', 'user7', '伊藤 健一', 'acc4', 'グローバルテック株式会社',
 'cat4', 'UX改修依頼', 'catd5', 'UI/UX改善提案', 'ch4', 'Chat/LLM',
 '多言語対応', 'システムの表示言語を日本語・英語・中国語に対応してほしいです。グローバル展開を予定しています。',
 'user6', '田中 美咲', 'stat3', '確認中', CURRENT_DATE + INTERVAL '30 days', NULL, NULL,
 NULL, NULL, NULL, FALSE, 'I18N-4048'),

('TCK-0049', NOW() - INTERVAL '29 days', 'user4', '高橋 三郎', 'acc2', 'XYZ株式会社',
 'cat3', '障害報告', 'catd4', 'システム障害', 'ch2', '電話',
 'セッションタイムアウトの問題', '作業中に頻繁にセッションがタイムアウトし、再ログインが必要になります。タイムアウト時間を延長できませんか？',
 'user1', '山田 太郎', 'stat4', '完了', CURRENT_DATE - INTERVAL '27 days', CURRENT_DATE - INTERVAL '28 days', 1.5,
 'resp3', '開発修正対応', 'セッションタイムアウト時間を30分から2時間に延長しました。', TRUE, NULL),

('TCK-0050', NOW() - INTERVAL '30 days', 'user8', '渡辺 さくら', 'acc5', 'イノベーションラボ株式会社',
 'cat5', '機能追加依頼', 'catd7', '新機能開発', 'ch5', 'Webフォーム',
 'チケットテンプレート機能', 'よく使うチケットのパターンをテンプレートとして保存し、新規作成時に利用できる機能を追加してください。',
 'user2', '鈴木 花子', 'stat4', '完了', CURRENT_DATE - INTERVAL '28 days', CURRENT_DATE - INTERVAL '29 days', 20.0,
 'resp5', '実装予定', 'テンプレート機能を実装し、本番環境にリリースしました。', FALSE, 'TMPL-4050');

-- チケット41-50の添付ファイル
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0041', 'index_error_log.txt', 'https://example.com/storage/TCK-0041/index_error_log.txt', NOW() - INTERVAL '26 days'),
  ('TCK-0043', 'highlight_mockup.png', 'https://example.com/storage/TCK-0043/highlight_mockup.png', NOW() - INTERVAL '2 days'),
  ('TCK-0044', 'user_permission_list.csv', 'https://example.com/storage/TCK-0044/user_permission_list.csv', NOW() - INTERVAL '28 days'),
  ('TCK-0046', 'import_error_sample.csv', 'https://example.com/storage/TCK-0046/import_error_sample.csv', NOW() - INTERVAL '1 day'),
  ('TCK-0050', 'template_design.pdf', 'https://example.com/storage/TCK-0050/template_design.pdf', NOW() - INTERVAL '30 days');

-- チケット41-50の履歴
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0041', NOW() - INTERVAL '26 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0041', NOW() - INTERVAL '25 days', 'user2', '鈴木 花子', '検索インデックスの再構築を実施し、問題を解決しました。'),
  ('TCK-0042', NOW() - INTERVAL '13 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0043', NOW() - INTERVAL '2 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0044', NOW() - INTERVAL '28 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0045', NOW() - INTERVAL '14 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0046', NOW() - INTERVAL '1 day', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0047', NOW() - INTERVAL '27 days', 'user2', '鈴木 花子', '新規チケット作成'),
  ('TCK-0048', NOW() - INTERVAL '10 days', 'user6', '田中 美咲', '新規チケット作成'),
  ('TCK-0049', NOW() - INTERVAL '29 days', 'user1', '山田 太郎', '新規チケット作成'),
  ('TCK-0050', NOW() - INTERVAL '30 days', 'user2', '鈴木 花子', '新規チケット作成');


-- 次回のチケットID用にシーケンスの値を更新
SELECT setval('ticket_id_seq', 50, true);
