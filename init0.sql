CREATE TABLE if NOT EXISTS posts (
    forum INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT
);
CREATE INDEX idx_posts ON posts(author, forum);
INSERT INTO posts VALUES (2, 'adam', 'adam text in mongodb test thread', 'Fri, 25 Oct 2018 17:00:15 GMT');
