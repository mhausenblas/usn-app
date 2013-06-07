#!/bin/bash -

###
# Manages the batch layer of the USN app.
#
#
# Usage: ./batch-layer.sh INIT | CHECK
#

function usage() {
	printf "Usage: %s INIT | CHECK\n" $0
}

function display_check_error() {
	printf "There seems to be an issue with the USN batch layer. "
	printf "Run CLEAN and then INIT again.\n"
}

function exec_hive_from_file() {
	hive -S -f $1 2>/dev/null
}

function usn_check() {
	check_file=check-result.tmp
	check_file_content=""
	exec_hive_from_file $USN_CHECK_BASE > $check_file
	if [ -f $check_file ] ; then
		check_file_content=$( cat "$check_file" )
		if  [[ $check_file_content = "499" ]] ; then
			printf "The USN batch layer seems OK.\n"
		else
			display_check_error
		fi
		rm $check_file
	else 
		display_check_error
	fi
}

# Some variable declarations
USN_CREATE=usn_create.hql
USN_DESTROY=usn_destroy.hql
USN_CHECK_BASE=usn_base_check.hql
USN_DUMP_BASE=usn_base_dump.hql

# Main script
case $1 in
 INIT )    exec_hive_from_file $USN_CREATE ; echo "USN batch layer created." ;;
 DESTROY ) exec_hive_from_file $USN_DESTROY ; echo "USN batch layer removed." ;;
 CHECK )   usn_check ;;
 * )       usage ; exit 1 ; ;;
esac
