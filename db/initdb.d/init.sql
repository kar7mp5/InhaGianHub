INSERT INTO facility (name) VALUES ('Main Hall') ON DUPLICATE KEY UPDATE name = name;
