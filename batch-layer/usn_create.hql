CREATE DATABASE IF NOT EXISTS usn;

USE usn;

DROP TABLE IF EXISTS usn_base;

CREATE TABLE usn_base (
 actiontime STRING,
 originator STRING,
 action STRING,
 network STRING,
 target STRING,
 context STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '|';

LOAD DATA LOCAL INPATH '../data/usn-base-data.csv' INTO TABLE usn_base;

DROP TABLE IF EXISTS usn_friends;

CREATE TABLE usn_friends AS
SELECT actiontime, originator AS username, network, 
       target AS friend, context AS note
FROM usn_base
WHERE action = 'ADD'
ORDER BY username, network, username;