CREATE TABLE if NOT EXISTS forums (
    id INTEGER PRIMARY KEY,
    name TEXT,
    creator TEXT
);
CREATE UNIQUE INDEX idx_forums ON forums(name, creator);
INSERT INTO forums VALUES (1, 'redis', 'alice');
INSERT INTO forums VALUES (2, 'mongodb', 'bob');
CREATE TABLE if NOT EXISTS threads (
    id INTEGER NOT NULL,
    forum INTEGER,
    title TEXT,
    creator TEXT,
    timestamp TEXT,
    PRIMARY KEY (id, forum),
    FOREIGN KEY(forum) REFERENCES forums(id)
        ON DELETE CASCADE
);
CREATE INDEX idx_threads ON threads(forum, creator);
INSERT INTO threads VALUES (1, 1, 'Does anyone know how to start Redis?', 'bob', 'Wed, 05 Sep 2018 16:22:29 GMT');
INSERT INTO threads VALUES (2, 1, 'Has anyone heard of Edis?', 'charlie', 'Tue, 04 Sep 2018 13:18:43 GMT');
CREATE TABLE if NOT EXISTS posts (
    id INTEGER NOT NULL,
    thread INTEGER,
    forum INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT,
    PRIMARY KEY (id, thread, forum),
    FOREIGN KEY(thread, forum) REFERENCES threads(id, forum)
        ON DELETE CASCADE
);
CREATE INDEX idx_posts ON posts(thread, forum, author);
INSERT INTO posts VALUES (1, 1, 1, 'bob', 'bob placeholder text', 'Wed, 05 Sep 2018 16:22:29 GMT');
INSERT INTO posts VALUES (2, 1, 1, 'alice', 'snarky alice response', 'Wed, 05 Sep 2018 16:34:46');
INSERT INTO posts VALUES (1, 2, 1, 'charlie', 'charlie placeholder text', 'Tue, 04 Sep 2018 13:18:43 GMT');
CREATE TABLE if NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
);
CREATE UNIQUE INDEX idx_users ON users(username);
INSERT INTO users VALUES ('adam', 'apple');
