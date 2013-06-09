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
NETWORKS_MAP = { 'I' : 'real life', 'T' : 'Twitter', 'L' : 'LinkedIn',
'F' : 'Facebook', 'G' : 'Google+'} 



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
		client.execute('SELECT actiontime, username, friend, network, note FROM usn_friends')
		rows = client.fetchAll()
		for row in rows:
			fields = row.split('\t')
			# turns actiontime=2012-09-11T21:04:23-07:00 and user=Ted
			# into row_key=Ted_2012-09-11
			row_key = fields[1] + '_' + fields[0].split('T')[0] # the row key
			a_name = fields[2] # a:name (the target)
			a_network = fields[3] # a:network
			a_comment = fields[4] # a:comment 
			print row_key + ' - ' + a_name + ' - ' + a_network + ' - ' + a_comment
			table = self.connection.table(TABLE_USN_FRIENDS) 
			table.put(row_key, {'a:name': a_name, 'a:network': a_network , 'a:comment': a_comment})
			
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
	
	def serve(self):
		menu_options = { 'u' : self.query_user, 'n' : self.query_network, 'l' : self.lookup, 's' : self.search, 'h' : self.show_help } 
		choice = "z"
		while choice != 'q': 
			try: 
				menu_options[choice]() 
			except KeyError:
				pass
			self.show_help()
			choice = raw_input("Your selection: ")

	def show_help(self):
		print "\n\nu ... user listings, n ... network listings, l ... lookup, s ... search, h ... help, q ... quit"
	
	def query_user(self):
		user = raw_input("List acquintances of which user?\nOne of: Ellen, John, Karen, Michael, Steve, Ted >")
		logging.debug('Selected user is %s' %user)
		self.scan_table(table_name=TABLE_USN_FRIENDS, start=user, stop=user+'z', cols=('a:name', 'a:network'))
		
	def query_network(self):
		user = raw_input("List acquintances of which user?\nOne of: Ellen, John, Karen, Michael, Steve, Ted >")
		logging.debug('Selected user is %s' %user)
		network = raw_input("From which network?\nOne of: I - in-real-life, T - Twitter, L - LinkedIn, F - Facebook, G - Google+ >")
		logging.debug('Selected network is %s' %network)
		self.scan_table(table_name=TABLE_USN_FRIENDS, start=user, stop=user+'z', cols=('a:name', 'a:network'), filter=network)

	def lookup(self):
		user = raw_input("List acquintances of which user?\nOne of: Ellen, John, Karen, Michael, Steve, Ted >")
		logging.debug('Selected user is %s' %user)
		start_date = raw_input("From when?\nIn the form YYYY-MM-DD, such as 2013-01-01 or only 2012 >")
		logging.debug('Start date is %s' %start_date)
		end_date = raw_input("(OPTIONAL) Until when?\nIn the form YYYY-MM-DD, such as 2013-01-01 or only 2012 >")
		logging.debug('End date is %s' %end_date)
		if not end_date:
			end_date = 'z'
		network = raw_input("(OPTIONAL) From which network?\nOne of: I - in-real-life, T - Twitter, L - LinkedIn, F - Facebook, G - Google+ >")
		logging.debug('Selected network is %s' %network)
		self.scan_table(table_name=TABLE_USN_FRIENDS, start=user+'_'+start_date, stop=user+'_'+end_date, cols='a', filter=network)

	def search(self):
		table = self.connection.table(TABLE_USN_FRIENDS)
		result_set_size = 0
		
		target = raw_input("The name of the person you want to search?\nName >")
		target = str(target)
		filter_str = 'SingleColumnValueFilter(\'a\',\'name\',=,\'regexstring:%s\',true,true)' %target

		logging.debug('Scanning %s for target %s' %(TABLE_USN_FRIENDS, filter_str))
		for key, data in table.scan(filter=filter_str):
			username = key.split('_')[0]
			print 'User \'%s\' has \'%s\' from %s in her or his network.' %(username, data['a:name'], NETWORKS_MAP[data['a:network']] )			
			logging.debug('Key: %s - Value: %s' %(key, str(data)))
			result_set_size = result_set_size + 1 
		print '*** Found %d matches in total' %result_set_size

	def scan_table(self, table_name, start, stop, cols, filter=None):
		"""Scans a HBase table using filter."""
		table = self.connection.table(table_name)
		result_set_size = 0
		
		if filter:
			if all(ord(c) < 128 for c in filter): # pure ASCII string
				p = filter
			else: # @@TODO: needs a more elegant way
				p = repr(filter)
				p = p[1:-1]
			filter_str = 'ValueFilter(=,\'substring:%s\')' %str(p)
			
			logging.debug('Scanning %s from %s to %s with %s' %(table_name, start, stop, filter_str))
			for key, data in table.scan(row_start=start, row_stop=stop, columns=cols, filter=filter_str):
				self.display_user_network_result(data)
				result_set_size = result_set_size + 1 
		else:
			logging.debug('Scanning %s from %s to %s' %(table_name, start, stop))
			for key, data in table.scan(row_start=start, row_stop=stop, columns=cols):
				self.display_user_network_result(data)
				result_set_size = result_set_size + 1 
		
		print '*** Found %d matches in total' %result_set_size
	
	def display_user_network_result(self, data):
		print "%s from %s" %(data['a:name'], NETWORKS_MAP[data['a:network']] )

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
			elif proxy_op == 'SERVE':
				usn_proxy.serve()
			else:
				print __doc__
		else: print __doc__
	except Exception, e:
		logging.error(e)
		sys.exit(2)
