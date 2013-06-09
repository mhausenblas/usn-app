# UberSocialNet - applying the Lambda Architecture

**Summary**

Recently, Nathan Marz introduced the Lambda Architecture for realising 
large-scale data processing applications. In this article, we step-by-step 
walk through how to build an application based on this architecture:
*UberSocialNet* (USN), a little helper tool that allows us to keep track of
where we know people from. USN lets us record if we happen to know someone 
from either the digital world, that is, social networks such as Twitter,
Facebook, LinkedIn, G+, etc. or the real life. The goal is that USN can serve 
more than one billion users while providing low-latency access to the 
annotations we keep about where and how we know people.

## The raw data

The [raw 
data](https://github.com/mhausenblas/usn-app/blob/master/data/usn-base-data.csv)
resides in the `data/` directory and has the following shape in the
base (CSV) format:

	timestamp,originator,action,network,target,context
	2012-03-12T22:54:13-07:00,Michael,ADD,I,Ora Hatfield,Some witty stuff here 
	2012-11-23T01:53:42-08:00,Michael,REMOVE,I,Marvin Garrison,Whatever note ...

with the following schema:

* `timestamp` is an ISO 8601 formatted datetime stamp that states when the 
action was performed (range: January 2012 till May 2013)
* `originator` is the name of the person who added or removed a person to or
from one of his or her networks
* `action` MUST be either `ADD` or `REMOVE`, self-explanatory. 
* `network` is a single character, MUST be one out of `{I, T, L, F, G}`, 
indicating the respective network where the action has been performed, with: 
 * `I` … in-real-life
 * `T` … Twitter
 * `L` … LinkedIn
 * `F` … Facebook
 * `G` … Google+
* `target` is the name of the person added or removed to or from the network
* `context` is a free-text comment, providing a hint why the person has been
added or where one has met the person in the first place

All fields are always present, that is, there are no optional fields. The test
data has been generated using [generatedata.com](http://www.generatedata.com/) 
in five runs totaling some 500 rows of raw data. 


## Generation of the layers

### Batch layer

Make sure you have Hive 0.10.0 installed or access to a setup (cluster, cloud) 
where it is running.

The raw data is first 
[pre-processed
](https://github.com/mhausenblas/usn-app/blob/master/data/usn-preprocess.sh) and 
[loaded](https://github.com/mhausenblas/usn-app/blob/master/hive-cmds.txt) into 
Hive:

	hive> CREATE TABLE usn_base (
	 actiontime STRING,
	 originator STRING,
	 action STRING,
	 network STRING,
	 target STRING,
	 context STRING
	) ROW FORMAT DELIMITED FIELDS TERMINATED BY '|';

	hive> LOAD DATA LOCAL INPATH 
	'/Users/mhausenblas2/Documents/repos/usn-app/data/usn-base-data.csv'
	INTO TABLE usn_base;

	hive> CREATE TABLE usn_friends AS
	      SELECT originator AS username, network, target AS friend, context AS note
	      FROM usn_base
	      WHERE action = 'ADD'
	      ORDER BY username, network, username;

### Serving layer

Make sure you have HBase 0.94.x installed or access to a setup (cluster, cloud) 
where it is running.

**Preparation** First you need to launch HBase and the Thrift server. 

Go to the HBase home directory and do the following:

	$ ./bin/start-hbase.sh 
	
	starting master, logging to /Users/mhausenblas2/bin/hbase-0.94.4/logs/hbase-mhausenblas2-master-Michaels-MacBook-Pro-2.local.out

	$ ./bin/hbase thrift start -p 9191
	13/05/31 09:39:09 INFO util.VersionInfo: HBase 0.94.4
	13/05/31 09:39:09 INFO util.VersionInfo: Subversion https://svn.apache.org/repos/asf/hbase/branches/0.94 -r 1428173
	13/05/31 09:39:09 INFO util.VersionInfo: Compiled by jenkins on Thu Jan  3 06:29:56 UTC 2013
	13/05/31 09:39:09 INFO thrift.ThriftServerRunner: Using default thrift server type
	13/05/31 09:39:09 INFO thrift.ThriftServerRunner: Using thrift server type threadpool
	...

**Init** First you need to initialize the USN table.

Note that you need to do the following from USN directories as shown below,
so `cd` respectively first.

Make sure Hive service is running from the USN batch layer directory:

	$ pwd
	/Users/mhausenblas2/Documents/repos/usn-app/batch-layer
	$ hive --service hiveserver
	Starting Hive Thrift Server
	...

Then,`cd` into the parent directory of the batch layer directory and
execute the following:

	$ pwd
	/Users/mhausenblas2/Documents/repos/usn-app
	$ python serving-layer.py localhost INIT
	...
	2013-06-07T06:02:53 Initialized USN tables in serving layer.

You can use the shell to verify if the serving layer has been initialized correctly:

	$ ./bin/hbase shell
	hbase(main):001:0> describe 'usn_friends'
	DESCRIPTION                                                                                          ENABLED
	 {NAME => 'usn_friends', FAMILIES => [{NAME => 'a', DATA_BLOCK_ENCODING => 'NONE', BLOOMFILTER => 'N true
	 ONE', REPLICATION_SCOPE => '0', VERSIONS => '3', COMPRESSION => 'NONE', MIN_VERSIONS => '0', TTL =>
	  '-1', KEEP_DELETED_CELLS => 'false', BLOCKSIZE => '65536', IN_MEMORY => 'false', ENCODE_ON_DISK =>
	  'true', BLOCKCACHE => 'false'}]}
	1 row(s) in 0.2450 seconds
	
	hbase(main):002:0> count 'usn_friends'
	499 row(s) in 0.0540 seconds
	
A sample query (scan, in HBase jargon) might look as follows:

	hbase(main):001:0> scan 'usn_friends', { COLUMNS => ['a'], FILTER => "ValueFilter(=,'substring:L')", STARTROW => 'Ted_2013-01'}
	ROW                                      COLUMN+CELL
	 Ted_2013-01-17                          column=a:comment, timestamp=1370630348723, value=urna et arcu imperdiet ullamcorper. Duis at lacus. Quisque purus
	 ...
	 Ted_2013-03-25                          column=a:network, timestamp=1370630348769, value=L
	8 row(s) in 0.0460 seconds

The above query translates into: give me all acquaintances of `Ted` in the
`LinkedIn` network, starting from January 2013 on. 

You can have a look at some more queries used in the demo user interface
on the [respective Wiki page](https://github.com/mhausenblas/usn-app/wiki/Serving-Layer).

Oh. And when you're done, don't forget to shut down HBase (again, from HBase home):

	$ ./bin/stop-hbase.sh


## Usage

### Dependencies 

The following components and tools are assumed to be available:

* Hive 0.10.x
* [Hiver](https://github.com/tebeka/hiver) for Python interaction
* HBase 0.94.x
* [HappyBase](https://github.com/wbolster/happybase) for Python interaction

Then, the pre-processing steps as explained above (batch and serving layer
generation) must be done.

### CLI User Interface

After you've prepared and init the batch and serving layers as described above
you can launch the user interface (pure CLI for now):

	$ ./usn-ui.sh
	This is USN v0.0
	
	
	u ... user listings, n ... network listings, l ... lookup, h ... help, q ... quit
	Your selection:

A recorded USN session from the CLI user interface is available here.

### License

All artifacts in this repository, including data and code are donated into
the Public Domain. The author would like to thank MapR Technologies for
sponsoring the work on the USN app.
