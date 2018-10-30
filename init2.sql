CREATE TABLE if NOT EXISTS posts (
    forum INTEGER,
    author TEXT,
    text TEXT,
    timestamp TEXT
);
CREATE INDEX idx_posts ON posts(author, forum);
INSERT INTO posts VALUES (1, 'charlie', 'charlie text in Edis thread', 'Tue, 04 Sep 2018 13:18:43 GMT');
