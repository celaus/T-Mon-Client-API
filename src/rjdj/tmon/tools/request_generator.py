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

from threading import Thread
import time
import random
import ConfigParser
from rjdj.tmon.client import TMonClient, TMonClientError

# Dummy data for simulating a certain number of requests on a web service

# Virtual URLs that are "called"
URLS = (
    "/",
    "/login",
    "/register",
    "/get/data",
    )

# Virtual source IPs that work as source addresses
IPS = (
    "192.168.0.1",
    "231.71.58.1",
    "91.48.8.7",
    "8.8.8.8",
    "9.9.9.9",
    "123.45.8.91",
    "188.154.5.32",
    )
    
# Real user agents as test data
UAS = (
    "Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405", 
    "Mozilla/5.0 (Linux; U; Android 2.2.1; fr-ch; A43 Build/FROYO) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3",
    "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3",
    )
    
 Users that are also included (or an empty string, simulating anonymous access)
USER = (
    "jsmith",
    "fmuller",
    "jdoe", 
    "", "", # double the chances of an empty request
    )
    
def send_request(client):
    """ Simulates a request and adds tracking data. """
    
    url = URLS[random.randint(0, len(URLS) - 1)]
    ip = IPS[random.randint(0, len(IPS) - 1)]
    ua = UAS[random.randint(0, len(UAS) - 1)]
    user = USER[random.randint(0, len(USER) - 1)]
    client.track(url = url, useragent = ua, ip = ip, username = user)

def run(tmon_client, num_of_req):
    """ Runs <num_of_req> requests per minute (in parallel) on <tmon_client>. """
    
    delay = num_of_req / 60 # seconds
    threads = []
    
    for num in xrange(num_of_req):
        t = Thread(target = send_request, 
                   args = (tmon_client, ))
        t.start()
        threads.append(t)
            
    for thread in threads:
        thread.join()
    
    raw_input("All done, any key to continue ...")
    
def run_from_commandline(path_to_file, *args):
    """ """
    
    client = None
    try:
        num_of_req = int(args[0])
        
        parser = ConfigParser.ConfigParser()
        parser.read(args[1])
        config = {}
        for name, value in parser.items("loadtest"):
            config.update({name: value})
        
        client = TMonClient(config)   
        run(client, num_of_req)
    except TMonClientError:
        print """Please provide a valid config file! See var/default.cfg for an example! """
        exit(1)
    except:
        print "USAGE: loadtest <number of requests per minute> <path to config>"
        exit(1)

