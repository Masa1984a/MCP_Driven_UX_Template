-- PostgreSQL数据库初始化脚本

-- 创建模式
CREATE SCHEMA IF NOT EXISTS mcp_ux;

-- 以下所有表都将在mcp_ux模式中创建
SET search_path TO mcp_ux;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  role VARCHAR(50) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 账户表
CREATE TABLE IF NOT EXISTS accounts (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 类别表
CREATE TABLE IF NOT EXISTS categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 类别详情表
CREATE TABLE IF NOT EXISTS category_details (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 状态表
CREATE TABLE IF NOT EXISTS statuses (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 接收渠道表
CREATE TABLE IF NOT EXISTS request_channels (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 响应类别表
CREATE TABLE IF NOT EXISTS response_categories (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_category VARCHAR(100),
  order_no INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 工单编号序列
CREATE SEQUENCE IF NOT EXISTS ticket_id_seq START 1;

-- 工单表
CREATE TABLE IF NOT EXISTS tickets (
  id VARCHAR(50) PRIMARY KEY,  -- 格式为"TCK-XXXX"
  reception_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
  requestor_id VARCHAR(50) NOT NULL REFERENCES users(id),
  requestor_name VARCHAR(100) NOT NULL,  -- 反规范化
  account_id VARCHAR(50) NOT NULL REFERENCES accounts(id),
  account_name VARCHAR(100) NOT NULL,  -- 反规范化
  category_id VARCHAR(50) NOT NULL REFERENCES categories(id),
  category_name VARCHAR(100) NOT NULL,  -- 反规范化
  category_detail_id VARCHAR(50) NOT NULL REFERENCES category_details(id),
  category_detail_name VARCHAR(200) NOT NULL,  -- 反规范化
  request_channel_id VARCHAR(50) NOT NULL REFERENCES request_channels(id),
  request_channel_name VARCHAR(50) NOT NULL,  -- 反规范化
  summary VARCHAR(200) NOT NULL,
  description TEXT,
  person_in_charge_id VARCHAR(50) NOT NULL REFERENCES users(id),
  person_in_charge_name VARCHAR(100) NOT NULL,  -- 反规范化
  status_id VARCHAR(50) NOT NULL REFERENCES statuses(id),
  status_name VARCHAR(50) NOT NULL,  -- 反规范化
  scheduled_completion_date DATE,
  completion_date DATE,
  actual_effort_hours NUMERIC(5,1),
  response_category_id VARCHAR(50) REFERENCES response_categories(id),
  response_category_name VARCHAR(100),  -- 反规范化
  response_details TEXT,
  has_defect BOOLEAN DEFAULT FALSE,
  external_ticket_id VARCHAR(50),
  remarks TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 附件表
CREATE TABLE IF NOT EXISTS attachments (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  file_name VARCHAR(255) NOT NULL,
  file_url VARCHAR(1000) NOT NULL,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 工单历史表（工单变更历史）
CREATE TABLE IF NOT EXISTS ticket_history (
  id SERIAL PRIMARY KEY,
  ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(id),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  user_id VARCHAR(50) REFERENCES users(id),
  user_name VARCHAR(100) NOT NULL,  -- 反规范化
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 变更字段历史表（工单历史的子表）
CREATE TABLE IF NOT EXISTS history_changed_fields (
  id SERIAL PRIMARY KEY,
  history_id INTEGER NOT NULL REFERENCES ticket_history(id),
  field_name VARCHAR(100) NOT NULL,
  old_value TEXT,
  new_value TEXT
);

-- 示例数据 - 用户
INSERT INTO users (id, name, email, role) VALUES
  ('user1', '李大明', 'daming.li@example.com', '负责人'),
  ('user2', '王小红', 'xiaohong.wang@example.com', '负责人'),
  ('user3', '张三', 'san.zhang@example.com', '请求者'),
  ('user4', '李四', 'si.li@example.com', '请求者'),
  ('user5', '陈经理', 'manager.chen@example.com', '管理员'),
  ('user6', '刘美玲', 'meiling.liu@example.com', '负责人'),
  ('user7', '赵强', 'qiang.zhao@example.com', '请求者'),
  ('user8', '吴小花', 'xiaohua.wu@example.com', '请求者');

-- 示例数据 - 账户
INSERT INTO accounts (id, name, order_no) VALUES
  ('acc1', '东方科技有限公司', 1),
  ('acc2', '中华电子股份有限公司', 2),
  ('acc3', '北京创新企业', 3),
  ('acc4', '环球技术集团', 4),
  ('acc5', '智能实验室有限公司', 5);

-- 示例数据 - 类别
INSERT INTO categories (id, name, order_no) VALUES
  ('cat1', '咨询', 1),
  ('cat2', '数据修正请求', 2),
  ('cat3', '故障报告', 3),
  ('cat4', '用户体验改进请求', 4),
  ('cat5', '功能增加请求', 5);

-- 示例数据 - 类别详情
INSERT INTO category_details (id, name, category_id, category_name, order_no) VALUES
  ('catd1', '门户、文章和搜索功能相关咨询', 'cat1', '咨询', 1),
  ('catd2', '支持管理相关咨询', 'cat1', '咨询', 2),
  ('catd3', '主数据修正请求', 'cat2', '数据修正请求', 1),
  ('catd4', '系统故障', 'cat3', '故障报告', 1),
  ('catd5', '界面/用户体验改进建议', 'cat4', '用户体验改进请求', 1),
  ('catd6', '搜索功能改进建议', 'cat4', '用户体验改进请求', 2),
  ('catd7', '新功能开发', 'cat5', '功能增加请求', 1),
  ('catd8', '集成功能增加', 'cat5', '功能增加请求', 2);

-- 示例数据 - 状态
INSERT INTO statuses (id, name, order_no) VALUES
  ('stat1', '已接收', 1),
  ('stat2', '处理中', 2),
  ('stat3', '确认中', 3),
  ('stat4', '已完成', 4);

-- 示例数据 - 接收渠道
INSERT INTO request_channels (id, name, order_no) VALUES
  ('ch1', '邮件', 1),
  ('ch2', '电话', 2),
  ('ch3', 'Teams', 3),
  ('ch4', '聊天/LLM', 4),
  ('ch5', '网页表单', 5);

-- 示例数据 - 响应类别
INSERT INTO response_categories (id, name, parent_category, order_no) VALUES
  ('resp1', '可从中国回复', '咨询', 1),
  ('resp2', '免费支持', '数据修正请求', 1),
  ('resp3', '开发修正处理', '故障报告', 1),
  ('resp4', '需要设计审查', '用户体验改进请求', 1),
  ('resp5', '计划实施', '功能增加请求', 1);

-- 示例数据 - 工单 1
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0001',
  NOW() - INTERVAL '5 days',
  'user3', '张三',
  'acc1', '东方科技有限公司',
  'cat1', '咨询',
  'catd1', '门户、文章和搜索功能相关咨询',
  'ch1', '邮件',
  '搜索功能无法正常工作',
  '在搜索框中输入特定关键词时，没有显示结果。\n重现步骤：\n1. 在首页搜索框中输入包含"特殊字符"的搜索词\n2. 点击搜索按钮\n3. 显示"没有搜索结果"',
  'user1', '李大明',
  'stat2', '处理中',
  CURRENT_DATE + INTERVAL '2 days',
  FALSE,
  'EXT-123'
);

-- 工单1的附件
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0001', 'error_screenshot.png', 'https://example.com/storage/error_screenshot.png', NOW() - INTERVAL '5 days');

-- 工单1的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '5 days', 'user1', '李大明', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0001', NOW() - INTERVAL '3 days', 'user1', '李大明', '开始调查。特殊字符转义处理可能有问题。');

-- 工单1历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (2, 'status', '已接收', '处理中');

-- 示例数据 - 工单 2
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
  'user4', '李四',
  'acc2', '中华电子股份有限公司',
  'cat2', '数据修正请求',
  'catd3', '主数据修正请求',
  'ch2', '电话',
  '用户主数据信息更新请求',
  '我公司的负责人已更改。请按以下方式更新：\n\n原负责人：王一郎\n新负责人：田五郎\n邮箱地址：goro.tian@zhonghua.co.cn\n电话号码：010-1234-5678',
  'user2', '王小红',
  'stat4', '已完成',
  CURRENT_DATE - INTERVAL '8 days',
  CURRENT_DATE - INTERVAL '9 days',
  1.5,
  'resp2', '免费支持',
  '主数据更新已完成。\n请确认变更内容。',
  FALSE
);

-- 工单2的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '10 days', 'user2', '王小红', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0002', NOW() - INTERVAL '9 days', 'user2', '王小红', '主数据更新已完成。已向客户发送确认邮件。');

-- 工单2历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (4, 'status', '已接收', '已完成');

-- 示例工单3
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0003',
  NOW() - INTERVAL '1 day',
  'user3', '张三',
  'acc1', '东方科技有限公司',
  'cat3', '故障报告',
  'catd4', '系统故障',
  'ch3', 'Teams',
  '仪表板无法显示',
  '从今天早上开始，访问仪表板时显示错误。\n错误消息："数据加载失败"\n\n多个用户都出现了相同的问题。',
  'user1', '李大明',
  'stat1', '已接收',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'INC-456',
  '需要紧急处理。'
);

-- 工单3的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0003', NOW() - INTERVAL '1 day', 'user1', '李大明', '创建新工单');

-- 示例数据 - 工单 4 (搜索相关问题)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id
) VALUES (
  'TCK-0004',
  NOW() - INTERVAL '2 days',
  'user7', '赵强',
  'acc4', '环球技术集团',
  'cat1', '咨询',
  'catd1', '门户、文章和搜索功能相关咨询',
  'ch4', '聊天/LLM',
  '全文搜索部分结果未命中',
  '使用全文搜索功能时，应该包含特定关键词的文章没有命中。\n重现步骤：\n1. 在搜索框中输入"操作手册"\n2. 点击搜索按钮\n3. 包含"操作手册"一词的文章没有显示在搜索结果中',
  'user6', '刘美玲',
  'stat2', '处理中',
  CURRENT_DATE + INTERVAL '5 days',
  TRUE,
  'BUG-789'
);

-- 工单4的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '2 days', 'user6', '刘美玲', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0004', NOW() - INTERVAL '1 day', 'user6', '刘美玲', '开始调查。发现特殊字符索引处理有问题。');

-- 工单4历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (6, 'status', '已接收', '处理中');

-- 示例数据 - 工单 5 (用户体验改进)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0005',
  NOW() - INTERVAL '7 days',
  'user8', '吴小花',
  'acc5', '智能实验室有限公司',
  'cat4', '用户体验改进请求',
  'catd6', '搜索功能改进建议',
  'ch1', '邮件',
  '希望定制搜索结果排序',
  '搜索结果目前按日期顺序显示，但希望能够按相关度、类别等进行排序。\n用户反馈"很难找到要找的东西"。',
  'user1', '李大明',
  'stat3', '确认中',
  CURRENT_DATE + INTERVAL '14 days',
  FALSE
);

-- 工单5的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '7 days', 'user1', '李大明', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '5 days', 'user1', '李大明', '确认了建议内容。正在制作新排序选项的模型。');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0005', NOW() - INTERVAL '2 days', 'user1', '李大明', '向申请者发送了模型，请求审查。');

-- 工单5历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (8, 'status', '已接收', '处理中');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (9, 'status', '处理中', '确认中');

-- 示例数据 - 工单 6 (性能问题)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect, external_ticket_id, remarks
) VALUES (
  'TCK-0006',
  NOW() - INTERVAL '3 days',
  'user3', '张三',
  'acc1', '东方科技有限公司',
  'cat3', '故障报告',
  'catd4', '系统故障',
  'ch3', 'Teams',
  '搜索功能性能下降',
  '自上周更新以来，搜索功能的响应速度明显下降。\n特别是返回大量搜索结果时可能需要10秒以上。\n附上APM工具日志。',
  'user2', '王小红',
  'stat2', '处理中',
  CURRENT_DATE + INTERVAL '1 day',
  TRUE,
  'PERF-456',
  '高优先级 - 影响多个用户'
);

-- 工单6的附件
INSERT INTO attachments (ticket_id, file_name, file_url, uploaded_at) VALUES
  ('TCK-0006', 'apm_logs.txt', 'https://example.com/storage/apm_logs.txt', NOW() - INTERVAL '3 days'),
  ('TCK-0006', 'performance_metrics.pdf', 'https://example.com/storage/performance_metrics.pdf', NOW() - INTERVAL '3 days');

-- 工单6的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '3 days', 'user2', '王小红', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0006', NOW() - INTERVAL '2 days', 'user2', '王小红', '开始性能分析。发现需要优化数据库查询。');

-- 工单6历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (12, 'status', '已接收', '处理中');

-- 示例数据 - 工单 7 (功能增加请求)
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
  'user4', '李四',
  'acc2', '中华电子股份有限公司',
  'cat5', '功能增加请求',
  'catd7', '新功能开发',
  'ch5', '网页表单',
  '实施高级搜索过滤器功能',
  '希望使用以下过滤器的高级搜索功能：\n- 日期范围\n- 文档类型\n- 标签/类别\n- 作者\n- 状态\n这将大大提高快速找到特定文档的能力。',
  'user1', '李大明',
  'stat4', '已完成',
  CURRENT_DATE - INTERVAL '10 days',
  CURRENT_DATE - INTERVAL '2 days',
  24.5,
  'resp5', '计划实施',
  '实施了高级搜索过滤器功能并部署到生产环境。用户现在可以使用多个条件筛选搜索结果。',
  FALSE
);

-- 工单7的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '15 days', 'user1', '李大明', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '12 days', 'user1', '李大明', '开始开发。创建了UI模型和后端API设计。');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0007', NOW() - INTERVAL '2 days', 'user1', '李大明', '功能实施完成并部署到生产环境。');

-- 工单7历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (14, 'status', '已接收', '处理中');

INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (15, 'status', '处理中', '已完成');

-- 示例数据 - 工单 8 (集成功能增加)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0008',
  NOW() - INTERVAL '4 days',
  'user7', '赵强',
  'acc4', '环球技术集团',
  'cat5', '功能增加请求',
  'catd8', '集成功能增加',
  'ch2', '电话',
  '通知用Slack API集成',
  '希望在以下时机能够与Slack进行实时通知集成：\n- 创建新工单时\n- 工单分配给团队成员时\n- 状态变更时\n- 添加评论时\n这将大大改善响应时间。',
  'user6', '刘美玲',
  'stat1', '已接收',
  CURRENT_DATE + INTERVAL '21 days',
  FALSE
);

-- 工单8的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0008', NOW() - INTERVAL '4 days', 'user6', '刘美玲', '创建新工单');

-- 示例数据 - 工单 9 (登录问题)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0009',
  NOW() - INTERVAL '6 days',
  'user4', '李四',
  'acc3', '北京创新企业',
  'cat1', '咨询',
  'catd2', '支持管理相关咨询',
  'ch1', '邮件',
  '登录功能相关问题',
  '关于忘记密码时的重置方法有咨询。具体是关于密码重置邮件无法送达这一点需要确认详情。',
  'user2', '王小红',
  'stat3', '确认中',
  CURRENT_DATE + INTERVAL '4 days',
  FALSE
);

-- 工单9的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0009', NOW() - INTERVAL '6 days', 'user2', '王小红', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0009', NOW() - INTERVAL '4 days', 'user2', '王小红', '正在确认邮件服务器设置。');

-- 工单9历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (17, 'status', '已接收', '确认中');

-- 示例数据 - 工单 10 (仪表板改进)
INSERT INTO tickets (
  id, reception_date_time, requestor_id, requestor_name, account_id, account_name,
  category_id, category_name, category_detail_id, category_detail_name,
  request_channel_id, request_channel_name, summary, description,
  person_in_charge_id, person_in_charge_name, status_id, status_name,
  scheduled_completion_date, has_defect
) VALUES (
  'TCK-0010',
  NOW() - INTERVAL '8 days',
  'user8', '吴小花',
  'acc5', '智能实验室有限公司',
  'cat4', '用户体验改进请求',
  'catd5', '界面/用户体验改进建议',
  'ch3', 'Teams',
  '仪表板图表显示期间设置',
  '报告了仪表板相关问题。症状是显示的图表期间设置方法这一现象发生。',
  'user1', '李大明',
  'stat2', '处理中',
  CURRENT_DATE + INTERVAL '7 days',
  FALSE
);

-- 工单10的历史
INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0010', NOW() - INTERVAL '8 days', 'user1', '李大明', '创建新工单');

INSERT INTO ticket_history (ticket_id, timestamp, user_id, user_name, comment) VALUES
  ('TCK-0010', NOW() - INTERVAL '6 days', 'user1', '李大明', '正在考虑期间选择UI的改进方案。');

-- 工单10历史的变更字段
INSERT INTO history_changed_fields (history_id, field_name, old_value, new_value) VALUES
  (19, 'status', '已接收', '处理中');

-- 下一个工单ID用序列值更新
SELECT setval('ticket_id_seq', 10, true);