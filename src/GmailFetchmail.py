#!/usr/bin/env python

#@PydevCodeAnalysisIgnore

import sys
import subprocess
import syslog
import traceback
import time
import re
import os
import Gmail

DEBUG = False

class GmailFetchmail:
	
	IDENT = 'GmailFetchmail'
	SENDMAIL_CMD = ['/usr/sbin/sendmail', '-i', '--']
	PID_FILE = "GmailFetchmail.pid"

	def __init__(self, username, password, localUsername):
                self.__pidFileCreated = False
		if self.__isRunning():
			raise 'already running'
		self.__createPidFile()

		self._username = username
		self._password = password
		self._localUsername = localUsername
		self._gmail = Gmail.Gmail(username = self._username, password = self._password)	
		self._gmail.login()
		self._sendmailCommand = GmailFetchmail.SENDMAIL_CMD
		self._sendmailCommand.append(self._localUsername)

	def __del__(self):
		self.__removePidFile()
			
	def initLog():
		syslog.openlog(GmailFetchmail.IDENT,  syslog.LOG_CONS | syslog.LOG_NOWAIT | syslog.LOG_PID, syslog.LOG_USER)
	initLog = staticmethod(initLog)
		
	def closeLog():
		syslog.closelog()
	closeLog = staticmethod(closeLog)
		
	def log(priority, message):
		syslog.syslog(priority, message)
		if DEBUG:
			print '%s %s: %s' % (time.time(), GmailFetchmail.IDENT, message)
	log = staticmethod(log)
	
	def fetch(self):
		GmailFetchmail.log(syslog.LOG_INFO, 'getting message ids...')
		
		ids = self._gmail.getMessageIds()
		
		GmailFetchmail.log(syslog.LOG_INFO, 'message ids: %s' % ids)

		for id in ids:			
			GmailFetchmail.log(syslog.LOG_INFO, 'retrieving message, id: %s' % id)

			message = self._gmail.getMessageOriginal(id)
				
			res = self._feedMessageToSendmail(message)
			if res == 0:
				GmailFetchmail.log(syslog.LOG_INFO, 'removing message, id: %s' % id)
					
				self._gmail.deleteMessage(id)
			
	def _feedMessageToSendmail(self, message):
	
		GmailFetchmail.log(syslog.LOG_INFO, 'opening sendmail pipe')
		
		popen = subprocess.Popen(self._sendmailCommand, stdin = subprocess.PIPE)
		
		popen.communicate(message)
		
		res = popen.returncode
		
		GmailFetchmail.log(syslog.LOG_INFO, 'sendmail return code: %s' % res)
		
		return res
	
	def __getPidFileName(self):
		return os.path.abspath(os.path.dirname(sys.argv[0])) + '/' + GmailFetchmail.PID_FILE;
	
	def __createPidFile(self):
		f = open(self.__getPidFileName(), 'w+')
		f.write(str(os.getpid()))
		f.close()
		self.__pidFileCreated = True
		
		GmailFetchmail.log(syslog.LOG_INFO, 'created pid file')
		
	def __removePidFile(self):
		if self.__pidFileCreated:
			os.remove(self.__getPidFileName())
			
			GmailFetchmail.log(syslog.LOG_INFO, 'removed pid file')
		
	def __isRunning(self):
		try:
			os.stat(self.__getPidFileName())
			
			f = open(self.__getPidFileName())
			pid = f.read()
			f.close()

			os.kill(int(pid), 0)
			
			return True
		except:
			return False
		
	def main(username, password, localUsername):
		try:
			GmailFetchmail.initLog()
			
			gmailFetchmail = GmailFetchmail(username, password, localUsername)
			
			gmailFetchmail.fetch()
		except:
			GmailFetchmail.log(syslog.LOG_ERR, 'exception in main(): %s' % traceback.format_exc())
	main = staticmethod(main)

if __name__ == '__main__':

	username = sys.argv[1]
	password = sys.argv[2]
	localUsername = sys.argv[3]
	
	GmailFetchmail.main(username, password, localUsername)
