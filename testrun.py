# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 09:51:55 2016

@author: mick
"""

import time
import threading

lock = threading.Lock()

def sleeper(i):
    print("thread {0} sleeps for 5 seconds".format(i))
    time.sleep(5)
    lock.acquire()
    print("thread {0} woke up.".format(i))
    lock.release()

for i in range(10):
    t = threading.Thread(target=sleeper,args=(i,))
    t.start()
