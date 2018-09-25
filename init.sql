CREATE TABLE if NOT EXISTS forums (
    id INTEGER PRIMARY KEY,
    name TEXT,
    creator TEXT
);
CREATE UNIQUE INDEX idx_forums ON forums(name, creator);
INSERT INTO forums VALUES (1, 'redis', 'alice');
INSERT INTO forums VALUES (2, 'mongodb', 'bob');
CREATE TABLE if NOT EXISTS threads (
    id INTEGER PRIMARY KEY,
    forum INTEGER,
    title TEXT,
    creator TEXT,
    timestamp TEXT,
    FOREIGN KEY(forum) REFERENCES forums(id)
);
CREATE INDEX idx_threads ON threads(forum, title, creator);
INSERT INTO threads VALUES (1, 1, 'Does anyone know how to start Redis?', 'bob', 'Wed, 05 Sep 2018 16:22:29 GMT');
INSERT INTO threads VALUES (2, 1, 'Has anyone heard of Edis?', 'charlie', 'Tue, 04 Sep 2018 13:18:43 GMT');
CREATE TABLE if NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    thread INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT,
    FOREIGN KEY(thread) REFERENCES threads(id)
);
CREATE INDEX idx_posts ON posts(author);
INSERT INTO posts VALUES (1, 1, 'bob', 'bob placeholder text', 'Wed, 05 Sep 2018 16:22:29 GMT');
INSERT INTO posts VALUES (2, 2, 'charlie', 'charlie placeholder text', 'Tue, 04 Sep 2018 13:18:43 GMT');
CREATE TABLE if NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
);
CREATE UNIQUE INDEX idx_users ON users(username);
INSERT INTO users VALUES ('adam', 'apple');
