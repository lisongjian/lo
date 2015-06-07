#encoding=utf8
import os
import sys
import IP
import traceback  

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# from tasks.startup import sms_code       
# from tasks.startup import push_msg       
# push_msg.apply_async(args=["13011114444", "this is the msg"], queue='jpush')    


# 
# x = IP.find("127.0.0.1"),
# print x.decode("utf8")
# imei = "865645028698195"
# from tasks.startup import wallad_callback
# 
# wallad_callback(914, imei)

a = 2
if a == 2:
    print "xxxxxxxxxx"
