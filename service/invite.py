#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Youmi 2014
#
# @author: chenjiehua@youmi.net
#

"""邀请相关

"""
import protocols

from models import users


class ShareHandler(protocols.JSONBaseHandler):
    """ 分享页面 """
    @protocols.unpack_arguments(with_phone=False)
    def get(self):
        try:
            tid = self.get_argument("tid", "")
            user_info = users.get_info_bytid(tid)
            if not user_info:
                raise Exception
            if user_info["username"] == None:
                user_info["username"] = ""
        except:
            tid = ""
        data = {
            "registerMoney": u"5",
            "inviteMoney": u"1",
            "inviteNum": tid,
            # TODO 后台设置正常下载地址
            "normalUrl": "http://storage.pgyer.com/9/c/4/1/4/9c4149faee6f4e9ee27d45d58311f23c.apk",
            # TODO 应用包下载地址
            "txUrl": "http://www.pgyer.com/bq4D",

        }
        self.render("../template/prentice/share-v2.html", data=data)


class PageHandler(protocols.JSONBaseHandler):

    def get(self):
        data = {
            "title" : "热点新闻",
            "name"  : "钱鹿锁屏",
            "apkurl": "http://storage.pgyer.com/9/c/4/1/4/9c4149faee6f4e9ee27d45d58311f23c.apk",
            "siu"   : "http://w.qiandeer.com/qd/static/lock/images/icon256.png",
            "adtxt" : "玩手机，轻松赚钱，不做骗你的小狗",
            "txUrl" : "http://a.app.qq.com/o/simple.jsp?pkgname=com.holysix.android.screenlock",
        }

        page = int(self.get_argument('article', 2))
        # 两篇文章
        version = page if page in [1, 2] else 2
        self.render("../template/share/banner-v%s.html" % version, data = data)
