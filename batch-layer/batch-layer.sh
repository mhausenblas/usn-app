#!/bin/bash -

###
# Sets up the batch layer of the USN app.
#
#
# Usage: ./batch-layer.sh
#

function usage() {
	printf "Usage: %s INIT | CLEAN\n" $0
}

function init_workspace() {
	printf "Initializing the USN app.\n"
}

function exec_hive_from_file() {
	printf "EXECUTING %s\n" $1
	hive -S -f $1
}

USN_CREATE_BASE=usn_create_base.hql

case $1 in
	INIT )	exec_hive_from_file $USN_CREATE_BASE  ;;
	* )		usage ; exit 1 ; ;;
esac
