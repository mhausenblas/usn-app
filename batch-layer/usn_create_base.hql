CREATE DATABASE IF NOT EXISTS usn;

USE usn;

CREATE TABLE usn_base (
 actiontime STRING,
 originator STRING,
 action STRING,
 network STRING,
 target STRING,
 context STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '|';