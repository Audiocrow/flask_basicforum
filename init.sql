CREATE TABLE if NOT EXISTS forums (id INTEGER PRIMARY_KEY, name TEXT, creator TEXT);
CREATE UNIQUE INDEX idx_forums ON forums(name);
INSERT INTO forums VALUES (1, 'redis', 'alice');
INSERT INTO forums VALUES (2, 'mongodb', 'bob');
CREATE TABLE if NOT EXISTS users (username TEXT PRIMARY_KEY, password TEXT);
CREATE UNIQUE INDEX idx_users ON users(username);
