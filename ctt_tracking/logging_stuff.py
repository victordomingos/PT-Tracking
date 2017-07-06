#!/usr/bin/env python3.6
# encoding: utf-8
"""
Create a user profile based on the current computer and some network info, for
logging purposes.

© 2017 Victor Domingos
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import logging
from requests import get
from datetime import datetime
from socket import gethostname
from getpass import getuser
from global_setup import OUR_LOCATIONS


"""
Fill this dictionary with known (fixed) IP addresses and the corresponding
names for your organization or work team. You can define it in another module
if it fits your purpose better. Just comment the following line and don't forget
to adjust the import clauses accordingly, as usual.
"""
#OUR_LOCATIONS = {'0.0.0.0': 'ExampleLocation',}


class basicLogInfo():
    def __init__(self):
        self.local_user = getuser()
        self.cpu = gethostname()

        try:
            self.myinfo = get("https://ipapi.co/json/",timeout=(1,2)).json()
            self.ip = self.myinfo['ip']
            self.city = self.myinfo['city']
            self.country = self.myinfo['country']
            self.org = self.myinfo['org']
        except Exception as e:
            logging.debug(e)
            self.ip = "Unknown_IP"
            self.city = "Unknown_City"
            self.country = "Unknown_Country"
            self.org = "Unknown_Org"

        if self.ip in OUR_LOCATIONS.keys():
            self.local_user = f"{self.local_user}@{self.cpu}({OUR_LOCATIONS[self.ip]})"
        else:
            self.local_user = f"{self.local_user}@{self.cpu}(?)"


    def generate_log_string(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        registo = f"{now} - {self.ip} [{self.local_user}] - {self.city} ({self.country}) - {self.org}"
        return registo


if __name__ == "__main__":
    """ A little example to show what this is doing... """
    user_info = basicLogInfo()
    logstr = user_info.generate_log_string()
    print(logstr)
