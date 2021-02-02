#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
from random import choice
from urlparse import urlparse
from datetime import datetime
from Helpers.graphic import *
from Helpers.utilities import percentage

def make_host_valid (host):
    host = host.strip()

    if not host.startswith("https://") and not host.startswith("http://"):
        host = "http://" + host

    if not host.endswith("/"):
        host = host + "/"

    return host

def get_base_hostname (url):
    url = urlparse (url)
    url = url.scheme + "://" + url.netloc

    return url

def check_target_connection (target, user_agent):
    target = get_base_hostname (target)

    try:
        requests.head(target, timeout=5, headers={"User-Agent": user_agent}).status_code
        return True
    except:
        return False

# This function get remote timestamp of the target http server (it store the data as datetime.datetime)
# I can probably find a better way to do this, but I don't want to rewrite the function :((
def get_remote_timestamp (target):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    target = get_base_hostname(target)
    dt = []

    try:
        raw_datetime = requests.head(target).headers["Date"].split(" ")
        dt.append(raw_datetime[3]) # Year
        dt.append([n + 1 for n, month in enumerate(months) if month == raw_datetime[2]][0]) # Month
        dt.append(raw_datetime[1]) # Day of the month
        dt.append(raw_datetime[4].split(":")[0]) # Hour
        dt.append(raw_datetime[4].split(":")[1]) # Minutes
        dt.append(raw_datetime[4].split(":")[2]) # Seconds

        # Converting the datetime list to a Python's datetime compatible tuple
        # Microseconds are not needed but required by datetime
        dt.append(0)
        dt = tuple([int(data) for data in dt])
        dt = datetime(*dt)

        return dt
    except:
        return False

# Salvare file di dirsearch con gli user agent ed estrarli da lì, non ha senso tenerli in memoria
def random_user_agent ():
    user_agents = open("txt/user-agents.txt", "r").read().splitlines()
    return choice(user_agents)

# Single threaded requester
def requester (base_url, filenames, cookie, user_agent="", proxy=""):
    len_filenames = len(filenames)

    proxy_dict = {}

    if proxy != "":
        proxy_dict = {"http": proxy, "https": proxy}

    try:
        for i, filename in zip(range(len_filenames), filenames):
            url = base_url + filename

            print "[%s%s%s] %s" % (bcolors.PINK, percentage(i, len_filenames) + "%", bcolors.ENDC, url)

            if i != len_filenames - 1:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")

            req = requests.head(url, timeout=5, cookies=cookie, headers={"User-Agent": user_agent}, proxies=proxy_dict, verify=False)

            if req.status_code == 200:
                notification ("FileGPS found your file! It is here: \033[4m%s\033[0m" % url, "found")
                return

        notification ("File not found..", "error")

    except KeyboardInterrupt:
        notification ("Stopped.", "removed")


def requester3 (target, cookie, user_agent, proxy, filename):
    try:
        url = target + filename

        proxy_dict = {}

        if proxy != "":
            proxy_dict = {"http": proxy, "https": proxy}

        req = requests.head(url, timeout=5, cookies=cookie, headers={"User-Agent": user_agent}, proxies=proxy_dict, verify=False)

        requester3.q.put ([url, req.status_code])
    except KeyboardInterrupt:
        sys.stdout = open(os.devnull, 'w')
        #sys.stdout.flush()

# Wrapper for the shared memory multiprocessing queue
def worker_init (q):
    requester3.q = q