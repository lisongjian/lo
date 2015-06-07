#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Youmi 2014
#
# @author: chenjiehua@youmi.net
#

"""设置页面相关

"""

import tornado.escape
import tornado.web
import urllib
import re

import protocols
from models import feedbacks, options


class DownloadHandler(protocols.JSONBaseHandler):
    """ 下载接口 """

    def get(self):
        # 有page则跳到下载页面，没有就直接下载
        page = self.get_argument('page', None)

        if page:
            self.write('准备开发')
        else:
            # TODO 改成后台修改
            # 判断是否微信
            ua   = self.request.headers['user-agent']
            p    = re.compile('MicroMessenger', re.IGNORECASE)
            iswx = p.search(ua)
            url  = "http://storage.pgyer.com/9/c/4/1/4/9c4149faee6f4e9ee27d45d58311f23c.apk" if not iswx else 'http://a.app.qq.com/o/simple.jsp?pkgname=com.holysix.android.screenlock'

            self.redirect(url)


class FAQHandler(protocols.JSONBaseHandler):
    """ 常见问题 """

    def get(self):
        data = {
            "title": "常见问题汇总"
        }
        self.render("../template/page/ask.html", data = data)


class GonglueHandler(protocols.JSONBaseHandler):
    """ 攻略 """

    def get(self):
        data = {
            "title": "赚钱攻略"
        }
        self.render("../template/page/gonglue.html", data = data)


