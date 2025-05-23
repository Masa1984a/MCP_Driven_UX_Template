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

-- 次回のチケットID用にシーケンスの値を更新
SELECT setval('ticket_id_seq', 8, true);
