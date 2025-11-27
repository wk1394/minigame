-- 给 users 表添加 role 字段
ALTER TABLE users ADD COLUMN role ENUM('admin', 'user') DEFAULT 'user' NOT NULL;

-- 查看表结构
DESCRIBE users;

-- 创建一个默认的 admin 用户（密码是 'admin123' 的 MD5: 0192023a7bbd73250516f069df18b500）
INSERT INTO users (username, password, role) VALUES ('admin', '0192023a7bbd73250516f069df18b500', 'admin');
INSERT INTO members (user_id, membership_type) VALUES (LAST_INSERT_ID(), 'vip');
