#!/usr/bin/env python
"""
USN - serving layer

Usage: python serving-layer.py host (INIT|CLEAR)

Example:
       python serving-layer.py localhost INIT

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2013-05-31
@status: init
"""

import sys, logging, datetime, time, happybase, hiver
from os import curdir, sep

###############
# Configuration
DEBUG = False

if DEBUG:
	FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
	logging.basicConfig(level=logging.DEBUG, format=FORMAT, 
datefmt='%Y-%m-%dT%I:%M:%S')
else:
	FORMAT = '%(asctime)-0s %(message)s'
	logging.basicConfig(level=logging.INFO, format=FORMAT, 
datefmt='%Y-%m-%dT%I:%M:%S')


#################################
# HBase interfacing classes

TABLE_USN_FRIENDS = 'usn_friends'
HBASE_THRIFT_PORT = 9191

class USNHBaseProxy(object):
	"""A proxy for managing USN tables in HBase (Thrift-based)"""
	def __init__(self, host): 
		self.host = host
		self.server_port = HBASE_THRIFT_PORT
		self.connection = happybase.Connection(host=self.host, 
port=self.server_port)
	
	def create_table(self, table_name, col_fam):
		"""Creates a table, if it does not yet exist."""
		current_tables = self.connection.tables()
		if table_name not in current_tables:
			self.connection.create_table(table_name, col_fam)
			if DEBUG: logging.debug('Created table %s.' 
%(table_name))
		else:
			if DEBUG: logging.debug('Table %s already exists!' 
%(table_name))
	
	def init(self):
		"""Inits the USN table."""
		# Create table that holds the view on acquaintances
		# It only has one column family called 'a' for acquaintance and
		# three columns: a:name (the target), a:network, and a:comment 
		self.create_table(table_name=TABLE_USN_FRIENDS, col_fam={'a': {}})

		# Query Hive and fill HBase table
		client = hiver.connect('localhost', 10000)
		client.execute('USE usn')
		client.execute('SELECT username, friend FROM usn_friends')
		rows = client.fetchAll()
		print rows
		logging.info('Initialized USN tables in serving layer.')
	
	def clear(self):
		"""Disables and drops the USN table."""
		current_tables = self.connection.tables()
		if TABLE_USN_FRIENDS in current_tables:
			self.connection.disable_table(TABLE_USN_FRIENDS)
			self.connection.delete_table(TABLE_USN_FRIENDS)
			logging.info('Cleared USN table.')
		else:
			logging.info('USN table did not exist, so no action required.')
	
	def scan_table(self, table_name, pattern=None):
		"""Scans a table using filter"""
		table = self.connection.table(table_name)
		if pattern:
			if all(ord(c) < 128 for c in pattern): # pure ASCII string
				p = pattern
			else: # @@TODO: needs a more elegant way
				p = repr(pattern)
				p = p[1:-1]
				
			filter_str = 'ValueFilter(=,\'substring:%s\')' %str(p)
			logging.info('Scanning table %s with filter %s' 
%(table_name, str(filter_str)))
			for key, data in table.scan(filter=filter_str):
				logging.info('Key: %s - Value: %s' %(key, 
str(data)))
		else:
			logging.info('Scanning table %s' %(table_name))
			for key, data in table.scan():
				logging.info('Key: %s - Value: %s' %(key, data))
	

#############
# Main script

if __name__ == '__main__':
	try:
		if len(sys.argv) == 3:
			hbase_host = sys.argv[1]
			proxy_op = sys.argv[2]
			usn_proxy = USNHBaseProxy(host=hbase_host) 
			if proxy_op == 'INIT':
				usn_proxy.init()
			elif proxy_op == 'CLEAR':
				usn_proxy.clear()
			else:
				print __doc__
		else: print __doc__
	except Exception, e:
		logging.error(e)
		sys.exit(2)
