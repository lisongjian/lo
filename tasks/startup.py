#encoding=utf8
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print "BASE_DIR=", BASE_DIR
# sys.path.append("/home/wu/Aptana Studio 3 Workspace/suoping")
sys.path.append(BASE_DIR)

from celery import Celery
import redis
import time
import yaml
import utils
import constants
import torndb
import urllib2

app = Celery('startup', broker='amqp://guest@localhost//')
app.config_from_object('tasks.celeryconfig')
 
#加载配置
try:
    config = yaml.load(file(constants.SETTINGS_FILE, 'r'), utils.YamlLoader)
except yaml.YAMLError as e:
    print "Error in configuration file: %s" % e
#链接redis
pool = redis.ConnectionPool(**config['redis'])
r = redis.Redis(connection_pool=pool)
 
@app.task(name="sms_code")
def sms_code(phone, t):
    '''t:1，表示注册；2、表示找回密码；3、表示绑定手机号码'''
    print "p=%s t=%s" % (phone, t)
    from modules import captcha
    try:
        succ ,code = captcha.send_sms_ytx(phone, config['ytx'])
        if not succ:
            if code == '112314':
                key_name = "suoping:many:%s" % phone
                r.setex(key_name, 1, 3600)
            log_path = config['log']['errsms']
            utils.loggers.use('errsms', log_path).info("code:%s phone:%s type:%s" % (code, phone, t) )
        else:
            key_name = "suoping:wait:%s" % phone
            r.setex(key_name, 1, 60)
            key_name = "suoping:code:%s" % phone
            r.setex(key_name, code, 600)
    except:
        import traceback 
        traceback.print_exc()
        
        
@app.task(name="push_msg")
def push_msg(phone, msg):
    try:
        utils.push(phone, msg)
    except:
        pass


@app.task(name="wallad_callback")
def wallad_callback(user_id, imei):
    from models import wallad_clicks 
    mysql = torndb.Connection(**config['mysql'])    

    wallad_click = mysql.get("SELECT * FROM `wallad_clicks` WHERE `idfa` = %s and appType=1 LIMIT 1", imei)
    if wallad_click:
        callback_url = wallad_click['callback_url']
        msg = ''
        try:
            msg = str(urllib2.urlopen(callback_url).read())
        except urllib2.HTTPError,e:
            msg = str(e.code)
        except urllib2.URLError,e:
            msg = str(e)
        utils.loggers.use('device', config['log']['adyoumi']).info('[youmi_callback]:'+msg)
        mysql.execute( "UPDATE `wallad_clicks` set `status`=1,`uid`=%s, `msg`=%s  WHERE `id`=%s", user_id, msg, wallad_click['id'])
    else:
        pass

        
@app.task(name="findaddress")
def findaddress(t, user_id, ip):
    '''t=1:注册时查找ip  t=2:兑换时查找ip'''
    import IP
    ip_address = IP.find(ip)   
    mysql = torndb.Connection(**config['mysql'])    
    if t == 1:
        mysql.execute( "UPDATE `users` set `ip_address`=%s  WHERE `uid`=%s", ip_address, user_id)
    
    
    
    
    
if __name__ == "__main__":
    print os.getcwd()
    print "test=%s"  % 21