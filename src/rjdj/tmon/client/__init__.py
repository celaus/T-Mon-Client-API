##############################################################################
#
# Copyright (c) 2011 Reality Jockey Ltd. and Contributors.
# This file is part of T-Mon Client.
#
# T-Mon Client is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# T-Mon Client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with T-Mon Client. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# -*- coding: utf-8 -*-

__docformat__ = "reStructuredText"

import urllib2
import urllib
import json
import base64
from sys import stderr
from Crypto.Cipher import AES
from threading import Thread

#
# Exceptions
#

# Error superclass
class TMonClientError(Exception):
    """ Super-class for errors of the client. """
    pass
    
# Configuration Errors
class InvalidSettings(TMonClientError):
    """ Configuration of the T-Mon Server is missing. """
    pass



#
# Implementation
#

# API class
class TMonClient(object):
    """
        An easy-to-use client for the T-Mon web service real-time tracking solution. 
        
        Example:
        >>> settings = { 
        ...              "secret" : "abcdef123456789abcdef12",   # AES secret for the web service
        ...              "webservice_id" : 1,                    # The ID of the web service to be monitored
        ...              "url" : "http://tracker.example.com/",  # The location of the T-Mon server
        ...            }
        >>> client = TMonClient(settings)
        ... client.track("/", "Mozilla/5.0 (iPad ...", "123.123.123.123") # send monitoring data
    
    """

    REMOTE_URL = "/data/collect" # URL of the RESTful collection interface

    # Keys for the tracking package 
    IP_KEY = 'ip'
    UA_KEY = 'useragent'
    USER_KEY = 'username'
    URL_KEY = 'url'

    # Keys for the settings dictionary
    SECRET_KEY = "secret"
    WSID_KEY = "wsid"
    SERVER_URL_KEY = "url"
    
    # Logging entry
    ERROR_MESSAGE = """
Error while tracking the webservice: %s
Parameters: 
    url: %s
    user agent: %s
    ip: %s
    username: %s

"""
    # Debug flag, it should ALWAYS be False outside testing
    DEBUG = False 
    
    def __init__(self, settings_dict):
        """ Create an instance of T-Mon client with the given settings. """
        if not isinstance(settings_dict, dict): 
            raise InvalidSettings(type(settings_dict))
        self.config = settings_dict
        if not (self.config and \
                 self.config[self.SERVER_URL_KEY] and \
                 self.config[self.WSID_KEY] and \
                 self.config[self.SECRET_KEY]):
            raise InvalidSettings()


    def track(self, url, user_agent, remote_ip, username = ""):
        """ Track a web service. """
        
        worker = Thread(target = self.__track_worker, args = (url, user_agent, remote_ip, username))
        worker.daemon = True
        worker.start()
        if self.DEBUG: worker.join()
        
    def __track_worker(self, url, user_agent, remote_ip, username):
        """ Makes sending the tracking request non-blocking! """
        
        data = { self.IP_KEY : remote_ip,
                 self.UA_KEY : user_agent,
                 self.URL_KEY: url }
        if username:
            data.update({ self.USER_KEY: username })
            
        wsid = int(self.config[self.WSID_KEY]) 
        encrypted_data = base64.b64encode(self.__encrypt(json.dumps(data)))
        try:
            self.__send(encrypted_data, wsid)
        except Exception as ex: 
            msg = self.ERROR_MESSAGE % (ex, url, user_agent, remote_ip, username)
            if self.DEBUG: print msg
            else: stderr.write(msg) 
    
    
    def __send(self, data, wsid):
        """ Sends the given data to the server. """
        
        server_url = self.config[self.SERVER_URL_KEY]
        server = ""
        if server_url.endswith("/"):
            server = self.REMOTE_URL[1:]
        else:
            server = self.REMOTE_URL
        
        server = "".join((server_url, server))
        urllib2.urlopen(server, urllib.urlencode({"data": data, "wsid": wsid })).read()


    def __encrypt(self, msg):
        """ Encrypts and Base64-encodes messages with the given secret (AES) """
        
        cipher = AES.new(self.config[self.SECRET_KEY], AES.MODE_CFB)
        return cipher.encrypt(msg)

