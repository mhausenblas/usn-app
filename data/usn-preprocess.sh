#!/bin/bash -

###
# Cleans up fields of a CSV file and prepares for Hive import, that is it 
# removes header row and delimits fields with '|'.
#
# The input CSV file has the following structure:
#
#  timestamp,originator,action,network,target,context
#  2012-03-12T22:54:13-07:00,Michael,ADD,I,Ora Hatfield,Some witty stuff here
#  ...
#
# The output CSV file then looks like following:
#
#  2012-03-12T22:54:13-07:00|Michael|ADD|I|Ora Hatfield|Some witty stuff here
#  ...
#
# All fields will be delimited by a '|' and the last field, _context_ 
# might contain one or more  ',' and hence needs to be truncated. 
#
# Usage: ./usn-preprocess.sh < usn-raw-data.csv > usn-base-data.csv
#

rowcounter=0

while read arecord ; do
if [ $rowcounter -gt 0 ]; then # make sure to drop the first row for Hive
 f0_timestamp=$(echo $arecord | cut -d',' -f1)
 f1_originator=$(echo $arecord | cut -d',' -f2)
 f2_action=$(echo $arecord | cut -d',' -f3)
 f3_network=$(echo $arecord | cut -d',' -f4)
 f4_target=$(echo $arecord | cut -d',' -f5)

 # now parse out the last field and only keep first fragment delimited by ','
 counter=0
 originalIFS=$IFS
 export IFS=","
 for subfield in $arecord ; do  
  if [ $counter -eq 5 ]; then
   f5_context=$subfield
   break
  fi
  (( counter++ ))	
 done
 export IFS=$originalIFS

 # now assemble the CSV record
 echo $f0_timestamp\|$f1_originator\|$f2_action\|$f3_network\|$f4_target\
\|$f5_context
fi
(( rowcounter++ ))	
done