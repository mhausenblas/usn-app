#!/bin/bash -

###
# Sets up the batch layer of the USN app.
#
#
# Usage: ./batch-layer.sh
#

function usage() {
	printf "Usage: %s\n" $0
}

function exec_hive_from_file() {
	printf "EXECUTING %s\n" $1
	# hive -S -f $2
}

function exec_hive_from_str() {
 hive -S -e $2
}

case $1 in
	INIT )	exec_hive_from_file $2 ;;
	* )		usage ; exit 1 ; ;;
esac
