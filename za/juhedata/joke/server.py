# -*- coding:utf8 -*-

import json, time, datetime
import copy
import tornado.web
import conf
import urllib
from conf import *
from logger import logger
from tornado import gen
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest
from tornado import template
import base64

APP_KEY = '59793b0bd5ce726074f53fa3beba7c78'

class WebPortal(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/getText', getTextHandler),
            (r'/getImg', getImgHandler),
        ]

        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)

class getTextHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):
        yesterday = datetime.date.today() - datetime.timedelta(1)
        yestertime = int(time.mktime(yesterday.timetuple()))

        loader = template.Loader(".")
        t = loader.load('joke.html')

        page = int(self.get_argument('page', 1))

        try:
            url = "http://japi.juhe.cn/joke/content/list.from"
            params = {
                "sort" : "desc",
                "page" : page,
                "pagesize" : 1,
                "time": str(yestertime),
                "key" : APP_KEY, #您申请的key
            }
            logger.info(params)

            http_client = AsyncHTTPClient()
            body = urllib.urlencode(params)
            req = HTTPRequest(url + '?' + body, method = 'GET')
            resp = yield gen.Task(http_client.fetch, req)
            if resp is None or resp.code != 200:
                logger.info('resp error, %s' % url)
                logger.info('resp error, %s, %s' % (resp.code, resp.body))
                self.write("get fail")
            else:
                b = resp.body.strip().replace('\r', '\\r').replace('\n', '\\n')
                #logger.info(a)
                res = json.loads(b, encoding = 'utf8', strict = False)
                if res['error_code'] == 0:
                    data = res['result']['data'][0]
                    data['nextPage'] = page + 1
                    self.write(t.generate(**data))
                else:
                    self.write(res)
        except Exception as e:
            logger.exception(e)

class getImgHandler(tornado.web.RequestHandler):
    @coroutine
    def get(self):

        yesterday = datetime.date.today() - datetime.timedelta(1)
        yestertime = int(time.mktime(yesterday.timetuple()))

        loader = template.Loader(".")
        t = loader.load('img.html')

        page = int(self.get_argument('page', 1))

        try:
            url = "https://japi.juhe.cn/joke/img/list.from"
            params = {
                "sort" : "desc",
                "page" : page,
                "pagesize" : 1,
                "time": str(yestertime),
                "key" : APP_KEY, #您申请的key
            }
            logger.info(params)

            http_client = AsyncHTTPClient()
            body = urllib.urlencode(params)
            req = HTTPRequest(url + '?' + body, method = 'GET')
            resp = yield gen.Task(http_client.fetch, req)
            if resp is None or resp.code != 200:
                logger.info('resp error, %s' % url)
                logger.info('resp error, %s, %s' % (resp.code, resp.body))
                self.write("get fail")
            else:
                b = resp.body.strip().replace('\r', '\\r').replace('\n', '\\n')
                #logger.info(a)
                res = json.loads(b, encoding = 'utf8', strict = False)
                if res['error_code'] == 0:
                    data = res['result']['data'][0]
                    data['nextPage'] = page + 1
                    self.write(t.generate(**data))
                else:
                    self.write(res)
        except Exception as e:
            logger.exception(e)


