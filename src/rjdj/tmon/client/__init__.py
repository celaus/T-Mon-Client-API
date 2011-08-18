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

import base64
import hashlib
import hmac
import json
import logging
import urllib
import urllib2
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
        ...              "wsid" : 1,                             # The ID of the web service to be monitored
        ...              "url" : "http://tracker.example.com/",  # The location of the T-Mon server
        ...            }
        >>> client = TMonClient(settings)
        ... client.track(**{"url": "/", 
        ...               "useragent": "Mozilla/5.0 (iPad ...", 
        ...               "ip": "123.123.123.123"}) # send monitoring data
    
    """

    REMOTE_URL = "/data/collect" # URL of the RESTful collection interface

    # Keys for the settings dictionary
    SECRET_KEY = "secret"
    WSID_KEY = "wsid"
    SERVER_URL_KEY = "url"
    
    # Logging entry
    ERROR_MESSAGE = """Error while tracking the webservice: %s
Fields: 
%s """
    
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


#    def track(self, url, user_agent, remote_ip, username = ""):
    def track(self, **fields):
        """ Track a web service. """
        if fields:
            worker = Thread(target = self.__track_worker, kwargs = fields)
            worker.daemon = True
            worker.start()
            if self.DEBUG: worker.join()
        
        
    def __track_worker(self, **data):
        """ Makes sending the tracking request non-blocking! """
        
        wsid = int(self.config[self.WSID_KEY]) 
        
        try:
            self.__send(json.dumps(data), wsid)
        except Exception as ex: 
            msg = self.ERROR_MESSAGE % (ex, data)
            if self.DEBUG: print msg
            else: logging.debug(msg) 
    
    
    def __send(self, data, wsid):
        """ Sends the given data to the server. """
        
        encoded_data = base64.b64encode(data)
        
        server_url = self.config[self.SERVER_URL_KEY]
        server = ""
        if server_url.endswith("/"):
            server = self.REMOTE_URL[1:]
        else:
            server = self.REMOTE_URL
        
        server = "".join((server_url, server))
        urllib2.urlopen(server, urllib.urlencode({"data": encoded_data, 
                                                  "wsid": wsid, 
                                                  "signature": self.__sign(data) 
                                                  })).read()


    def __sign(self, msg):
        """ Encrypts and Base64-encodes messages with the given secret (AES) """
        
        return hmac.new(str(self.config[self.SECRET_KEY]), msg, hashlib.sha1).hexdigest()

