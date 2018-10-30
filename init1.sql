CREATE TABLE if NOT EXISTS posts (
    forum INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT
);
CREATE INDEX idx_posts ON posts(author, forum);
INSERT INTO posts VALUES (1, 'bob', 'bob text in Redis thread', 'Wed, 05 Sep 2018 16:22:29 GMT');
INSERT INTO posts VALUES (1, 'alice', 'snarky alice response in Redis thread', 'Wed, 05 Sep 2018 16:34:46');
