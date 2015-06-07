#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Youmi
#
# @author chenyongjian@youmi.net
#
import time
import yaml
import utils
import redis
import constants
from utils import YamlLoader

def main():
    KEY = "suoping:jpush"
    try:
        config = yaml.load(file(constants.SETTINGS_FILE, 'r'), YamlLoader)
    except yaml.YAMLError as e:
        print "Error in configuration file: %s" % e
    pool = redis.ConnectionPool(**config['redis'])
    r = redis.Redis(connection_pool=pool)
    log_path = config['log']['push']
    while True:
        info = r.hgetall(KEY)
        #utils.loggers.use('push', log_path).info(str(info))
        if not info:
            time.sleep(0.1)
            continue
        else:
            for i in info :
                try:
                    utils.push(i,info[i])
                except:
                    utils.loggers.use('push', log_path).info("[error: %s : %s]" % ( str(info[i]), str(i) ) )
                finally:
                    r.hdel(KEY, i)
if __name__ == "__main__":
        main()
