DROP TABLE IF EXISTS forums;
CREATE TABLE forums (
    id int,
    name text,
    creator text,
    PRIMARY KEY (id)
);
CREATE INDEX forum_idx_creator ON forums (creator);
CREATE TYPE post (
    author text,
    text text,
    timestamp text
);
DROP TABLE IF EXISTS threads;
CREATE TABLE threads (
    id int,
    forum int,
    title TEXT,
    creator TEXT,
    timestamp TEXT,
    posts list<FROZEN<post>>,
    PRIMARY KEY (id, forum)
) WITH CLUSTERING ORDER BY (forum ASC);
CREATE INDEX idx_threads_forum ON threads(forum);
CREATE INDEX idx_threads_creator ON threads(creator);
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT
);
INSERT INTO users (username, password) VALUES ('adam', 'apple');
