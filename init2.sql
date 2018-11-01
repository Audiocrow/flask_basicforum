CREATE TABLE if NOT EXISTS posts (
    forum INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT
);
CREATE INDEX idx_posts ON posts(author, forum);
