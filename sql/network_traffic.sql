-- 创建网卡流量监控表
CREATE TABLE network_traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_name VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    mac_address VARCHAR(50),
    upload_speed REAL NOT NULL,
    download_speed REAL NOT NULL,
    upload_total INTEGER,
    download_total INTEGER,
    status INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入示例数据
INSERT INTO network_traffic (interface_name, ip_address, mac_address, upload_speed, download_speed, upload_total, download_total, status, create_time)
VALUES
('eth0', '192.168.1.10', '00:0C:29:3A:5B:7C', 1024.50, 5120.75, 1073741824, 2147483648, 1, '2023-10-27 10:00:00'),
('eth0', '192.168.1.10', '00:0C:29:3A:5B:7C', 1100.20, 5300.40, 1073742824, 2147484648, 1, '2023-10-27 10:01:00'),
('eth1', '192.168.1.11', '00:0C:29:3A:5B:7D', 2048.00, 10240.00, 536870912, 1073741824, 0, '2023-10-27 10:01:00');