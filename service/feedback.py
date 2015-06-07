#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright Youmi 2014
#
# @author: lisongjian@youmi.net
#

"""任务信息相关

"""
import protocols
from models import users, tasks, orders, feedbacks
from modules import reward


class FeedbackHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def post(self):
        desc = self.arguments.get('feedback_text')
        feedbacks.new_feedback(self.current_user['uid'], 0, '', desc, 1)
        self.return_success()

class QuestionHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        pass

class ShareHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        task = tasks.get_task_info(self.current_user['uid'], 2)
        if not task:
            earn = tasks.get_task_byid(2)
            orders.new_global_order(
                self.current_user['uid'], self.current_user['points'], earn,
                1, '恭喜您完成新手任务-首次分享,获得奖励')
            tasks.new_task(self.current_user['uid'], 2)
            users.add_tt_points(self.current_user['uid'], earn)
            reward.today_earn(self.current_user['uid'], earn)
        return self.return_success()

class ArticleHandler(protocols.JSONBaseHandler):
    @protocols.unpack_arguments()
    def get(self):
        #temp = []
        """article = {}
        article['token_ids'] = 1
        article['points'] = 20
        article['title'] = "明天进行2015年的高考预演"
        article['desc'] = "描述"
        article['article_url'] = "http://www.niaogebiji.com/article-7107-1.html"
        article['image_url'] = "http://static.qiandeer.com/w/screen/7.jpg"
        temp.append(article)"""
        temp = feedbacks.get_article_share()
        return self.return_result({'ts':temp})

