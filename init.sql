CREATE TABLE if NOT EXISTS forums (
    id INTEGER PRIMARY KEY,
    name TEXT,
    creator TEXT
);
CREATE UNIQUE INDEX idx_forums ON forums(name, creator);
INSERT INTO forums VALUES (1, 'redis', 'alice');
INSERT INTO forums VALUES (2, 'mongodb', 'bob');
CREATE TABLE if NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
);
CREATE UNIQUE INDEX idx_users ON users(username);
INSERT INTO users VALUES ('adam', 'apple');
