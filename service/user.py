#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Youmi 2014
#
# @author: lisongjian@youmi.net
#

"""用户信息相关

"""
import protocols
import utils
import constants
import IP
import re
import time
import urllib2
from datetime import date
import os
import random
import datetime
from PIL import Image
from models import users, orders, options, invites, tasks, wallad_clicks, channel, imei
from modules import captcha, reward

class CodeHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments(with_phone=False)
    def post(self):
        params = {}
        for key in ['phone', 'type', 'imei']:
            params[key] = self.arguments.get(key, "")
        version_code = self.arguments.get("version_code", 0)
        if version_code<8:
            return self.return_error(constants.ERR_IN_VERSION)
        
        #检测手机号和Imei是否重复
        if params['type'] == '1':   #新注册用户
            info = users.get_info_byphone(params['phone'])
            if info:
                if info['platform'] == 1 or info['platform']==0:     # Android or unknown
                    return self.return_error(constants.ERR_HAD_PHONE)
            #imei是否重复
            imei = users.check_imei(params['imei'])
            if imei:
                return self.return_error(constants.ERR_HAD_IMEI)
        if params['type'] == '2':
            pass
        #检测发送频率(1分钟内重发)
        if not captcha.check_freq_phone(params['phone']):
            return self.return_error(constants.ERR_CAPTCHA_FREQUENCY)
        #检测发送频率(1天内发送过多)
        if not captcha.check_many_phone(params['phone']):
            return self.return_error(constants.ERR_CAPTCHA_MANY)

####deprecated on 2015/06/03 by wukai
#         succ ,code = captcha.send_sms_ytx(params['phone'], self.config['ytx'])
#         if not succ:
#             if code == '112314':
#                 return self.return_error(constants.ERR_CAPTCHA_MANY)
#             log_path = self.config['log']['errcode']
#             utils.loggers.use('errcode', log_path).info(`params['phone']`+ `code`)
#             return self.return_error(constants.ERR_CAPTCHA_FAIL)
#         else:
#             key_name = "suoping:wait:%s" % params['phone']
#             self.redis.setex(key_name, 1, 60)
#             key_name = "suoping:code:%s" % params['phone']
#             self.redis.setex(key_name, code, 600)
#             self.return_success()

        #短信发送命令加入celery任务队列
        from tasks.startup import sms_code       
        sms_code.apply_async(args=[params['phone'], params['type']], queue='sms')    
        #因为异步不能获取发送状态码，全部返回成功状态
        self.return_success()


class SignHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments(with_phone=False)
    def post(self):
        params = {}
        for key in ['phone', 'smscode', 'password', 'imei', "channel" ,'version_code']:
            params[key] = self.arguments.get(key, "")
        version_code = self.arguments.get("version_code", 0)
        if version_code<8:
            return self.return_error(constants.ERR_IN_VERSION)
        err = captcha.check_sms(params['phone'], params['smscode'])
        if err:
            return self.return_error(err)
        err = self._check_input(params['phone'], params['imei'])
        if not err:
            #pwd = utils.encrypt_pwd(params['password'], None)
            # print `pwd` + 'en_pwd'
            ip = self.request.remote_ip
            log_path = self.config['log']['userip']
            utils.loggers.use('userip', log_path).info("%s : %s \r\n" % (params['phone'], ip))
#             ip_address = IP.find(ip)
            ip_address = "temp"  #IP.find(ip)
            data = channel.get_id(str(params['channel']))
            if not data:
                pkg = 0
            else:
                pkg = int(data['id'])
            
            #新建用户
            user_id = users.new_user(ip, ip_address, params['phone'], params['password'], params['imei'], pkg)
            
            #查找用户ip对应的地址; 塞入任务队列
            try:
                from tasks.startup import findaddress       
                findaddress.apply_async(args=[1, user_id, ip], queue='ipfind')      #1:代表这是用户新注册时的查询
                log_path = self.config['log']['test']
                utils.loggers.use('test', log_path).info("ok ip=%s id=%s" % (ip, user_id))
            except Exception, e:
                log_path = self.config['log']['test']
                utils.loggers.use('test', log_path).info(str(e))
                        
            #如果是有米积分墙,给其发回调; 塞入回调任务队列
            if pkg == 4:
                try:
                    from tasks.startup import wallad_callback
                    wallad_callback.apply_async(args=[user_id, params['imei']], queue='wallad')    
                except:
                    pass
            
            
#             wallad_click = wallad_clicks.get_callback_byimei(params['imei'])
#             if wallad_click:
#                 callback_url = wallad_click['callback_url']
#                 msg = ''
#                 try:
#                     msg = str(urllib2.urlopen(callback_url).read())
#                 except urllib2.HTTPError,e:
#                     msg = str(e.code)
#                 except urllib2.URLError,e:
#                     msg = str(e)
#                 utils.loggers.use('device', self.config['log']['adyoumi']).info('[youmi_callback]:'+msg)
#                 self.db.execute(
#                     "UPDATE `wallad_clicks` set `status`=1,`uid`=%s, `msg`=%s \
#                     WHERE `id`=%s", user_id, msg, wallad_click['id'])
#                 wallad_clicks.set_user_pkg(user_id, 4)

            return self.return_success()
        else:
            return self.return_error(err)

    def _check_input(self, phone, imei):
        # 检测手机号码和imei的合法性
        err = None
        reg = '^((13[0-9])|(14[5,7])|(15[^4,\\D])|(17[0,6-8])|(18[0-9]))\\d{8}$'
        try:
            re.search(reg,phone).group(0)
        except Exception:
            err = constants.ERR_INVALID_PHONE
        #try:
        #    re.search('\\d{15}',imei).group(0)
        #except Exception:
        #    err = constants.ERR_IMEI_INVALID
        return err


class UicHandler(protocols.JSONBaseHandler):
    '''邀请奖励'''
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        for key in ['phone', 'uic']:
            params[key] = self.arguments.get(key, "")
        # print `params`
        rate = int(options.get('rate'))
        if not self.current_user:
            self.return_error(constants.ERR_NO_PHONE)
            return
        if params['uic'] != 'null':
            # print '+5'
            # 一级邀请
            user_info = users.get_info_bytid(params['uic'])
            if not user_info:
                self.return_error(constants.ERR_IVCODE_INVALID)
                return
            # 师徒关系必须为同一平台(iOS,Android)
            if user_info['platform'] == self.current_user['platform'] and user_info['platform'] != 0:
                uid = int(user_info['uid'])
                users.set_invite(self.current_user['uid'], uid, user_info['parent'])
                orders.new_global_order(uid, user_info['points'],0,2,u'恭喜!您成功收取一名徒弟！')
                data = orders.get_otype_orders(self.current_user['uid'], 4, 0, 1)
                if not data:
                    bonus = 6   #有推荐码奖励6元
                    orders.new_global_order(self.current_user['uid'], 0 ,bonus*int(rate), 4, u'新手红包')
                    users.add_tt_points(self.current_user['uid'], bonus*int(rate))
                    users.set_bonus(self.current_user['uid'], bonus)    #标记用户的奖励为6元，方便结算时数据统计；
                    key_name = "suoping:earn:%s:%s" % (self.current_user['uid'], date.today().strftime("%Y%m%d"))
                    rate = int(options.get('rate'))
                    data = self.redis.get(key_name)
                    if not data:
                        self.redis.setex(key_name, "%.2f" % bonus , 86400)
                    else:
                        self.redis.setex(key_name, "%.2f" %((float(data)+(float(bonus*date)/int(rate)))), 86400)
                # 判断新手收徒任务
                task = tasks.get_task_info(uid, 3)
                if not task:
                    earn = tasks.get_task_byid(3)
                    orders.new_global_order(
                        uid, user_info['points'], earn, 1, '首次收徒奖励')
                    tasks.new_task(uid, 3)
                    users.add_iv_points(uid, earn)
                    key_name = "suoping:earn:%s:%s" % (uid, date.today().strftime("%Y%m%d"))
                    rate = int(options.get('rate'))
                    data = self.redis.get(key_name)
                    if not data:
                        self.redis.setex(key_name, "%.2f" %(float(earn)/int(rate)), 86400)
                    else:
                        self.redis.setex(key_name, "%.2f" %((float(data)+(float(earn)/int(rate)))), 86400)

                self._add_invite(uid,son=1)
                # 二级邀请
                if user_info['parent']:
                    grandfather = users.get_info(user_info['parent'])
                    orders.new_global_order(user_info['parent'],grandfather['points'],0,2,u'恭喜!您成功收取一名徒孙！',grandfather['platform'])
                    self._add_invite(user_info['parent'], grandson=1)
                return self.return_result({"msg": "恭喜您成为钱鹿锁屏的用户，您获得新手红包奖励"})
                #return self.return_success()
            else:
                self.return_error(constants.ERR_IVCODE_INVALID)
                return
        else:
            data = orders.get_otype_orders(self.current_user['uid'], 4, 0, 1)
            if not data:
                key_name = "suoping:earn:%s:%s" % (self.current_user['uid'], date.today().strftime("%Y%m%d"))
                rate = int(options.get('rate'))
                data = self.redis.get(key_name)
                bonus = 5   #无推荐码奖励5元
                if not data:
                    self.redis.setex(key_name, "%.2f" %(float(bonus*int(rate))/int(rate)), 86400)
                else:
                    self.redis.setex(key_name, "%.2f" %((float(data)+(float(bonus*date)/int(rate)))), 86400)
                orders.new_global_order(self.current_user['uid'],0,bonus*int(rate),4,u'新手红包')
                users.add_tt_points(self.current_user['uid'],bonus*int(rate))
                users.set_bonus(self.current_user['uid'], bonus)    #标记用户的奖励为5元，方便结算时数据统计；
            #return self.return_success()
            return self.return_result({"msg": "恭喜您成为钱鹿锁屏的用户，您获得新手红包奖励"})


    def _add_invite(self, uid, son=0, grandson=0):
        """ 增加邀请人数、记录 """
        users.add_invite(uid, son, grandson)
        today = date.today().strftime("%Y%m%d")
        if invites.get_invite(uid, today):
            invites.add_invite(uid, son, grandson)
        else:
            invites.new_invite(uid, son, grandson)


class LoginHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        code = self.arguments.get('imei', "")
        pwd = self.arguments.get('password', "")
        rate = int(options.get('rate'))
        params = {}
        for key in ['phone', 'password']:
            params[key] = self.arguments.get(key, "")
        version_code = self.arguments.get("version_code", 0)
        if version_code<8:
            return self.return_error(constants.ERR_IN_VERSION)
        if not self.current_user:
            self.return_error(constants.ERR_NO_PHONE)
            return
        if pwd == self.current_user['pwd']:
            #判断月份
            limit_month(self)
            #重置IMEI
            self._reset_imei(params['phone'],code)
            imei_limit = imei.get_imei_byphone(params['phone'])
            #判断设备
            d = imei.get_imei_byphone(params['phone'])
            if str(d['imei']) != str(code):
             #三次机会
                if imei_limit['status'] == 3:
                    return self.return_error(constants.ERR_IN_TIME)
                else:
                    return self.return_error(constants.ERR_IN_CHANGE)
            data = orders.get_otype_orders(self.current_user['uid'], 4, 0, 1)
            if not data:
                self._today_earn(self.current_user['uid'], 5*int(rate))
                orders.new_global_order(self.current_user['uid'],0,5*int(rate),4,u'新手红包')
                users.add_tt_points(self.current_user['uid'],5*int(rate))
            #添加记录最后登录时间，计算活跃
            #users.set_last_login(self.current_user['uid'],datetime.datetime.now())
            #添加记录IMEI
            imei.set_imei(self.current_user['uid'], self.current_user['phone'], code)
            return self.return_success()
        else:
            return self.return_error(constants.ERR_IN_PWD)

    def _today_earn(self, uid, points):
        """ 缓存记录今日赚取 """
        key_name = "suoping:earn:%s:%s" % (uid, date.today().strftime("%Y%m%d"))
        rate = int(options.get('rate'))
        data = self.redis.get(key_name)
        if not data:
            self.redis.setex(key_name, "%.2f" %(float(points)/int(rate)), 86400)
        else:
            self.redis.setex(key_name, "%.2f" %((float(data)+(float(points)/int(rate)))), 86400)

    def _reset_imei(self, phone, code):
        count = imei.get_imei_limit(phone)
        if int(count['total'] == 0):
            imei.set_imei_limit(phone, code)

class CheckDeviceHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        return self.return_success()
        params = {}
        for key in ['phone', 'password', 'imei']:
            params[key] = self.arguments.get(key, "")
        version_code = self.arguments.get("version_code", 0)
        if version_code<8:
            return self.return_error(constants.ERR_IN_VERSION)
        #重置IMEI
        self._reset_imei(params['phone'],params['imei'])
        #判断月份
        limit_month(self)
        imei_limit = imei.get_imei_byphone(params['phone'])
        #三次机会
        if imei_limit['status'] == 3:
            return self.return_error(constants.ERR_IN_TIME)
        elif str(imei_limit['imei']) != str(params['imei']):
            return self.return_error(constants.ERR_IN_CHANGE)
        else:
            return self.return_success()

    def _reset_imei(self, phone, code):
        count = imei.get_imei_limit(phone)
        if int(count['total'] == 0):
            imei.set_imei_limit(phone, code)

def limit_month(req_handler):
    limit = req_handler.redis.get("suoping:limit:month")
    if not limit:
        data = imei.get_limit_time()
        day = time.strptime(data['limit_date'],"%Y-%m-%d %H:%M:%S")
        month = time.strftime("%m", day)
        req_handler.redis.set("suoping:limit:month", str(month))
        check_limit_month(req_handler,str(month))
    else:
        check_limit_month(req_handler,str(limit))

def check_limit_month(req_handler,month):
    today = date.today()
    now_month = today.strftime("%m")
    datetiming = today.strftime("%Y-%m-%d %H:%M:%S")
    if str(now_month) != str(month):
        req_handler.redis.set("suoping:limit:month", now_month)
        imei.update_limit_time(datetiming)
        imei.update_imei_limit()

class DeviceHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        for key in ['phone', 'password', 'imei', 'smscode']:
            params[key] = self.arguments.get(key, "")
        err = captcha.check_sms(params['phone'], params['smscode'])
        if not err:
            imei.update_status_limit(params['phone'],params['imei'])
            return self.return_success()
        else:
            return self.return_error(err)

class ChpwdHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        #print utils.encrypt_pwd('2', '123')
        #print utils.validate_pwd.('X')
        for key in ['phone', 'old_password', 'new_password']:
            params[key] = self.arguments.get(key, "")
        # base34 之后再保存密码
        if params['old_password'] == self.current_user['pwd']:
            new_pwd = params['new_password']
            users.update_pwd(self.current_user['uid'], new_pwd)
            return self.return_success()
        else:
            return self.return_error(constants.ERR_IN_PWD)


class LostpwdcodeHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        for key in ['phone']:
            params[key] = self.arguments.get(key, "")
            # print `params[key]` + `key`
#         err = captcha.check_freq_phone(params['phone'])
#         if err == False:
#             return self.return_error(constants.ERR_CAPTCHA_FREQUENCY)
        
        #检测发送频率(1分钟内重发)
        if not captcha.check_freq_phone(params['phone']):
            return self.return_error(constants.ERR_CAPTCHA_FREQUENCY)
        #检测发送频率(1天内发送过多)
        if not captcha.check_many_phone(params['phone']):
            return self.return_error(constants.ERR_CAPTCHA_MANY)                
        #短信发送命令加入celery任务队列
        from tasks.startup import sms_code       
        sms_code.apply_async(args=[params['phone'], "2"], queue='sms')    #2为找回密码
        #因为异步不能获取发送状态码，全部返回成功状态
        self.return_success()

        
        
#         succ ,code = captcha.send_sms_ytx(params['phone'], self.config['ytx'])
#         if not succ:
#             if code == '112314':
#                 return self.return_error(constants.ERR_CAPTCHA_MANY)
#             log_path = self.config['log']['errcode']
#             utils.loggers.use('errcode', log_path).info(`params['phone']`+ `code`)
#             return self.return_error(constants.ERR_CAPTCHA_FAIL)
#         else:
#             key_name = "suoping:wait:%s" % params['phone']
#             self.redis.setex(key_name, 1, 60)
#             key_name = "suoping:code:%s" % params['phone']
#             self.redis.setex(key_name, code, 600)
#             self.return_success()

class ChecksmsHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments(with_phone=False)
    def post(self):
        params = {}
        for key in ['phone', 'sms_code']:
            params[key] = self.arguments.get(key, "")
        # print `params`
        err = captcha.check_sms(params['phone'], params['sms_code'])
        if not err:
            return self.return_success()
        else:
            return self.return_error(err)



class LostpwdHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        for key in ['phone', 'new_password']:
            params[key] = self.arguments.get(key, "")
        new_pwd = params['new_password']
        users.update_pwd(self.current_user['uid'], new_pwd)
        return self.return_success()


class NewtaskHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        params = {}
        for key in ['phone']:
            params[key] = self.arguments.get(key, "")
            # print `params[key]` + `key`
        missions = []
        rate = int(options.get('rate'))
        mission = tasks.get_task()
        u_task = tasks.user_task(self.current_user['uid'])
        exchange = orders.get_otype_orders(self.current_user['uid'], 3, 0, 1)
        if exchange:
            task = tasks.get_task_info(self.current_user['uid'], 5)
            if not task:
                earn = tasks.get_task_byid(5)
                orders.new_global_order(
                    self.current_user['uid'], self.current_user['points'], earn,
                    1, '恭喜您完成新手任务-首次兑换,获得奖励')
                tasks.new_task(self.current_user['uid'], 5)
                users.add_tt_points(self.current_user['uid'], earn)
                reward.today_earn(self.current_user['uid'], earn)
        for m in mission:
            flag = False
            for u in u_task:
                if u['task_id'] == m['id']:
                    missions.append({
                        "labels" : u'已完成',
                        "type" : m['id'],
                        "earn" : "%.2f" % (float(m['earn'])/int(rate)),
                        "status" : 1,
                        "desc": m['desc'],
                        #"nums": int(time.time()-(1422000000/random.randint(1,10))),
                        "nums": str(random.randint(400,500)) + u'万人完成',
                    })
                    flag = True
            if flag == False:
                missions.append({
                        "labels" : m['labels'],
                        "type" : m['id'],
                        "earn" : "%.2f" % (float(m['earn'])/int(rate)),
                        "status" : 0,
                        "desc": m['desc'],
                        #"nums": int(time.time()-(1422000000/random.randint(1,10))),
                        "nums": str(random.randint(400,500)) + u'万人完成',
                    })

                #else:
                #    missions.append({
                #        "labels" : m['labels'],
                #        "type" : m['id'],
                #        "earn" : m['earn'],
                #        "status" : 0
                #    })
        #Aorders = orders.get_global_orders(self.current_user['uid'])
        #for o in Aorders:
        #    tasks.append({
        #        "lables": o['note'],
        #        "type": o['otype'],
        #        "earn": "%.2f" % (int(o['points'])/ float(rate)),
        #        "status": 1,
        #    })
        self.return_result({
            "ts": missions
        })


class UserConfigHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        params = {}
        for key in ['phone', 'imei', 'imsi']:
            params[key] = self.arguments.get(key, "")
        version_code = self.arguments.get("version_code", 0)
        if int(version_code)<8:
            return self.return_error(constants.ERR_IN_VERSION)
        timestamp = int(time.time() * 1000)
        base_url = self.config['url']['base']
        uid = self.current_user['uid']
        rate = int(options.get('rate'))
        icon_url = ''
        if self.current_user['headimg'] :
            icon_url = base_url + self.current_user['headimg']
        points = int (self.current_user['points']/float(rate))
        appKey = self.config['duiba']['appKey']
        appSecret = self.config['duiba']['appSecret']
        params = {'uid': uid, 'credits': points, 'appSecret': appSecret, \
                  'appKey': appKey, 'timestamp': timestamp}
        sign = utils.md5_sign(params)
        url = "http://www.duiba.com.cn/autoLogin/autologin?uid=%s&credits=%s&appKey=%s&sign=%s&timestamp=%s" \
                % (uid, points, appKey, sign, timestamp)
        exchange = {"url": url,}
        invitation = {"uic": self.current_user['tid'],
                    "url": url,
                    }
        self.return_result({
            "exchange": exchange,
            "invitation": invitation,
            "uid": self.current_user['uid'],
            "usericon": icon_url,
        })


class QbsHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        version_code = self.arguments.get("version_code", 0)
        if int(version_code)<8:
            return self.return_error(constants.ERR_IN_VERSION)
        rate = int(options.get('rate'))
        today = date.today().strftime("%Y%m%d")
        uid = self.current_user['uid']
        key_name = "suoping:earn:%s:%s" % (uid, today)
        # print `key_name`
        data = self.redis.get(key_name)
        #print `data`
        today_earn = "%.2f" % (float(data) if data else 0 )
        #添加记录最后登录时间，计算活跃
        users.set_last_login(self.current_user['uid'],datetime.datetime.now())
        self.return_result({
            "balance": "%.2f" % (float(self.current_user['points'])/int(rate)),
            "disciple":"%.2f" % (float(self.current_user['iv_points'])/int(rate)),
            #"uid": self.current_user['uid']
            "today": today_earn,
        })


class QosHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        params = {}
        for key in ['fts', 'lts', 'type', 'act', 'n', 'phone']:
            params[key] = self.arguments.get(key, "")
            # print `params[key]` + `key`
        otype = int(params['type'])
        Aorders = []
        all_orders = []
        rate = int(options.get('rate'))
        desc = ''
        if otype == 0:
            desc = u'全部收入累计'
            #Aorders = orders.get_global_orders(self.current_user['uid'])
            #设计分页
            data_count = orders.count_global_orders(self.current_user['uid'])
            size = 20
            page_count = int(round(data_count[0]['count']/size))
            page = int(params['n'])
            if page_count == 0 :
                page_count = 1
            #if page > page_count:
            #    page = page_count
            #elif page < 1:
            #    page = 1
            offset = (page-1)*size
            Aorders = orders.get_global_orders(self.current_user['uid'],offset,size)
        else:
            if params['type'] == '1':
                desc = u'任务收入累计'
            elif params['type'] == '2':
                desc = u'学徒分成累计'
            elif params['type'] == '3':
                desc = u'兑换总额'
            #Aorders = orders.get_otype_orders(self.current_user['uid'], otype)
            data_count = orders.count_otype_orders(self.current_user['uid'],otype)
            size = 20
            page_count = int(round(data_count[0]['count']/size))
            page = int(params['n'])
            if page_count == 0 :
                page_count = 1
            #if page > page_count:
            #    page = page_count
            #elif page < 1:
            #    page = 1
            offset = (page-1)*size
            Aorders = orders.get_otype_orders(self.current_user['uid'],otype,offset,size)
        total = 0
        for o in Aorders:
            # TODO 上拉下拉加载更多有问题
            all_orders.append({
                "msg": o['note'],
                "time": str(o['record_time']),
                "amount": "%.2f" % (int(o['points'])/ float(rate)),
            })
            total +=o['points']
        total = "%.2f" % (total/float(rate))
        if otype == 0:
            total = "%.2f" % (self.current_user['points']/float(rate))
        fts = params['fts']
        lts = 0
        if params['act'] == '0':
            fts = time.time()
            lts = time.time()
        elif params['act'] == '1' or params['act'] == '2':
            lts = time.time()
        if params['act'] == '1':
            return self.return_result({})
        return self.return_result({"list": all_orders, "fts": int(fts), "lts": int(lts), "total": total, "desc": desc, })


class LogoutHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        return self.return_success()

class IconHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        params = {}
        for key in ['phone', 'icon']:
            params[key] = self.arguments.get(key, "")
        #fh = open("/static/gofree.png", "wb")
        #fh.write(params['icon'].decode('base64'))
        #fh.close()
        width = 100
        uid_hash = utils.md5(self.current_user['uid'])
        img_dir = 'static/headimg/%s/%s' % (uid_hash[:2], uid_hash[2:4])
        filename = utils.md5(str(time.time()+random.randint(10000, 99999)))
        img_file = '%s/%s.png' % (img_dir, filename)
        # 创建文件夹
        img_path = os.path.join(constants.BASE_DIR, img_dir)
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        f = open(os.path.join(constants.BASE_DIR, img_file), 'wb+')
        f.write(params['icon'].decode('base64'))
        f.close()
        im = Image.open(os.path.join(constants.BASE_DIR, img_file))
        ratio = float(width)/im.size[0]
        height = int(im.size[1]*ratio)
        nim = im.resize((width, height), Image.BILINEAR)
        nim.save(os.path.join(constants.BASE_DIR, img_file))
        users.update_avatar(self.current_user['uid'], '/'+img_file)
        base_url = self.config['url']['base']
        url = base_url + '/' + img_file
        # print `url` + 'url'
        return self.return_result({"url": url})


class DetailHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        params = {}
        for key in ['phone']:
            params[key] = self.arguments.get(key, "")
        # print `params[key]` + `key`
        base_url = self.config['url']['base']
        today = date.today().strftime("%Y%m%d")
        iv_today = invites.get_invite(self.current_user['uid'], today)
        rate = int(options.get('rate'))
        invite_earn = "%.2f" % (self.current_user['iv_points'] / float(rate))
        tudi ={ "today":iv_today['sons'] if iv_today else 0, "total":self.current_user['sons'],}
        tusun = {"today":iv_today['grandsons'] if iv_today else 0,"total":self.current_user['grandsons'],}
        invitation = {"url": base_url + '/share?tid=' + str(self.current_user['tid']) + '&fromother=1',"code": self.current_user['tid'],}
        #logo = 'http://pgy-app-icons.qiniudn.com/image/view/app_icons/caf1b702398e3713b0fb3e3d4549e9db/120'
        logo = 'http://w.qiandeer.com/qd/static/lock/images/lock-logo.png'
        return self.return_result({
            "tudi": tudi,
            "tusun":tusun,
            "logo": logo,
            "balance": invite_earn,
            "invitation": invitation,
        })

class MainInfosHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        version_code = self.arguments.get("version_code", 0)
        if int(version_code)<8:
            return self.return_error(constants.ERR_IN_VERSION)
        rate = int(options.get('rate'))
        today = date.today().strftime("%Y%m%d")
        uid = self.current_user['uid']
        key_name = "suoping:earn:%s:%s" % (uid, today)
        data = self.redis.get(key_name)
        today_earn = "%.2f" % (float(data) if data else 0 )
        #添加记录最后登录时间，计算活跃
        users.set_last_login(self.current_user['uid'],datetime.datetime.now())
        user_balance = {
            "balance": "%.2f" % (float(self.current_user['points'])/int(rate)),
            "disciple":"%.2f" % (float(self.current_user['iv_points'])/int(rate)),
            "today": today_earn,
        }

        timestamp = int(time.time() * 1000)
        base_url = self.config['url']['base']
        rate = int(options.get('rate'))
        icon_url = ''
        if self.current_user['headimg'] :
            icon_url = base_url + self.current_user['headimg']
        points = int (self.current_user['points']/float(rate))
        appKey = self.config['duiba']['appKey']
        appSecret = self.config['duiba']['appSecret']
        params = {'uid': uid, 'credits': points, 'appSecret': appSecret, \
                  'appKey': appKey, 'timestamp': timestamp}
        sign = utils.md5_sign(params)
        url = "http://www.duiba.com.cn/autoLogin/autologin?uid=%s&credits=%s&appKey=%s&sign=%s&timestamp=%s" \
                % (uid, points, appKey, sign, timestamp)
        exchange = {"url": url,}
        invitation = {"uic": self.current_user['tid'],
                    "url": url,
                    }
        user_config = {
            "exchange": exchange,
            "invitation": invitation,
            "uid": self.current_user['uid'],
            "usericon": icon_url,
        }

        image_list = [
            {
                "imageUrl":"http://www.qipaox.com/tupian/200810/20081051924582.jpg",
                 "website":"http://www.baidu.com"
            },
            {
                "imageUrl":"http://www.bz55.com/uploads1/allimg/120312/1_120312100435_8.jpg",
                "website":"http://www.baidu.com"
            },
            {
                "imageUrl":"http://img2.pconline.com.cn/pconline/0706/19/1038447_34.jpg",
                "website":"http://www.baidu.com"
            }
        ]
        return self.return_result({
            "user_balance" : user_balance,
            "user_config"  : user_config,
            "image_list"   : image_list
        })

