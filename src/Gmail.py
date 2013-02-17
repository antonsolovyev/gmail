#!/bin/env python

import re
import mechanize as ClientCookie
import ClientForm

class Gmail:
        '''
        Retrieve messages from Gmail account. Works with Acme Inc auth system and mail domain. Adjust for your own purposes.
	'''
        
        URL = 'https://mail.google.com/a/acme.com/'

        def __init__(self, username = "", password = ""):
                '''
        	'''
                self._username = username
                self._password = password
                self._cookieJar = ClientCookie.LWPCookieJar()
    
                opener = ClientCookie.OpenerFactory(ClientCookie.SeekableResponseOpener).build_opener(ClientCookie.HTTPCookieProcessor(self._cookieJar))
                ClientCookie.install_opener(opener)

        def login(self):
                '''
                Perform login
        	'''
                req = ClientCookie.Request(Gmail.URL)
                res = ClientCookie.urlopen(req)
                self._cookieJar.extract_cookies(res, req)
        
                form = ClientForm.ParseResponse(res, backwards_compat = False)[0]
      
                form['USER'] = self._username
                form['PASSWORD'] = self._password

                req2 = form.click()
                res2 = ClientCookie.urlopen(req2)
    
                # ClientForm screws up here
                html = res2.read()
                res2.seek(0)	    	   
                samlResponse = re.search(r'name="SAMLResponse">(.*)</textarea>', html, re.S).group(1)	    
                form2 = ClientForm.ParseResponse(res2, backwards_compat = False)[0]
                form2['SAMLResponse'] = samlResponse
                
                req3 = form2.click()
                res3 = ClientCookie.urlopen(req3)            
    
                html2 = res3.read()
                url = re.search(r'<noscript><a href="(.*)">Continue</a></noscript>', html2, re.S).group(1)
                url = re.sub('\&amp\;', '&' , url)
                req4 = ClientCookie.Request(url)
                res4 = ClientCookie.urlopen(req4)
    
                pageData = res4.read()
                
                if re.search('Passwd', pageData) and re.search('Email', pageData):
                        raise Exception("Login failed. (Wrong username/password?)")
        
        def retrievePage(self, url):
                '''
                Retrieve a page
                '''
                req = ClientCookie.Request(url)
                res = ClientCookie.urlopen(url)
        
                self._cookieJar.extract_cookies(res, req)
        
                pageData = res.read()
                
                return pageData
        
        def getMessageIds(self):
                '''
                Return list of message IDs (strings)
                '''
                pageData = self.retrievePage(Gmail.URL)
        
                # The pattern to find message ids is: <input type=checkbox name=t value="xxxxx">
                res = re.findall('<input\s+type=checkbox\s+name=t\s+value="(.*)">', pageData)
                
                return res
        
        def getMessageOriginal(self, id):
                '''
                Return original message by ID
                '''
                res = self.retrievePage(Gmail.URL + '?' + 'v=om&th=' + id)
                
                res = re.sub('^\s+', '', res, re.S)
                
                return res
        
        def getMessage(self, id):
                '''
                Return message HTML page by ID
                '''
                res = self.retrievePage(Gmail.URL + '?' + 'v=c&th=' + id)
                
                return res
        
        def deleteMessage(self, id):
                '''
                Delete message by ID
                '''
                for cookie in self._cookieJar:
                        if cookie.name == 'GMAIL_AT':
                                gmailAt = cookie.value
                
                self.retrievePage(Gmail.URL + '?' + 'a=dm&m=' + id + '&at=' + gmailAt)

if __name__ == '__main__':
        
        gmail = Gmail(username = 'XXXXX', password = 'XXXXX')
        
        gmail.login()
        
        ids = gmail.getMessageIds()
        print '-----> ids: %s' % ids
        
        for id in ids:
                print '-----> id: %s, message:\n%s' % (id, gmail.getMessageOriginal(id))
                print '-----> deleting id: %s' % id
                gmail.deleteMessage(id)
