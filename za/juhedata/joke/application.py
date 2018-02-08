import json
import tornado
import signal
import time
import random
import urllib
from tornado import gen
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.ioloop import IOLoop
from redisclient import Redis
from logger import logger
from assemble import *
from conf import *
from filter import ReceiverFilter, UnsubscribeFilter
from blackuser import BlackUserFilter
from exception import WorkerException,FakeSuccess
import smtplib
import dao
from errmsg import *
import base64

CLEAR_TIME = 60 * 10

class Worker:
    def __init__(self):
        self.terminate = False
        self.concurrentJobs = {} #{'email_id':'timestamp', 'email_id':'timestamp',...}
        self.idle = False
        self.filters = [ReceiverFilter(), UnsubscribeFilter(),BlackUserFilter()]
    
    def runLoop(self):
        if self.terminate:
            logger.info('%d messages left' % len(self.concurrentJobs))
            if len(self.concurrentJobs) == 0:
                logger.info('stop worker')
                tornado.ioloop.IOLoop.instance().stop()
            else:
                IOLoop.instance().add_timeout(time.time() + 1, self.runLoop)
            return

        if self.idle:
            logger.info("idle")
            IOLoop.instance().add_timeout(time.time() + 1, self.runLoop)
            self.idle = False
            return

        if len(self.concurrentJobs) >= MAX_CONCURRENT_JOBS:
            logger.info("full, concurrent jobs %d, %d" % (len(self.concurrentJobs), MAX_CONCURRENT_JOBS))
            self.checkCurrentJobs()
            IOLoop.instance().add_timeout(time.time() + 0.5, self.runLoop)
            return

        IOLoop.instance().add_timeout(time.time() + 0.01, self.runLoop)

        self.processNextMessage()

    def checkCurrentJobs(self):
        jobs = self.concurrentJobs.copy()
        for email_id,timestamp in jobs.iteritems():
            now = time.time()
            if now - timestamp > CLEAR_TIME:
                del self.concurrentJobs[email_id]
                logger.info('debug:remove %s in currentJobs',email_id)

    
    def statCacheHitRatio(self):
        logger.info('-------------stat cache hit ratio---------------') 
        objs = [('UserInfo', dao.UserInfo.instance()), \
                ('AppStatus', dao.AppStatus.instance()),\
                ('GlobalBounceReceiver', dao.GlobalBounceReceiver.instance()),\
                ('BounceReceiver', dao.BounceReceiver.instance()),\
                ('UserPrivateKey', dao.UserPrivateKey.instance()),\
                ('Unsubscribe', dao.Unsubscribe.instance()),\
                ('Category', dao.Category.instance())]

        for obj in objs:
            logger.info(obj[0])
            logger.info("memory: count: %d/%d, ratio:%.3f" % obj[1].memCacheHitRatio())
            logger.info("redis:  count: %d/%d, ratio:%.3f" % obj[1].redisCacheHitRatio())

    def start(self):
        tornado.ioloop.PeriodicCallback(self.statCacheHitRatio, 3600000).start()
        IOLoop.instance().add_timeout(time.time() + 0.01, self.runLoop)
        IOLoop.instance().start() 

    def stop(self):
        self.terminate = True

    @coroutine
    def fetchMsg(self):
        res = None
        try:
            http_client = AsyncHTTPClient()
            response = yield http_client.fetch('http://%s/worker' % SCHEDULER)
            if response.body != 'none':
                res = json.loads(response.body)
        except Exception as e:
            logger.exception(e)

        raise gen.Return(res)     
    
    @coroutine
    def sendToOutbound(self, msg):
        try:
            http_client = AsyncHTTPClient()
            data = {}
            data['email_id'] = msg['email_id']
            data['mail_from'] = msg['mail_from']
            data['rcpt_to']  = msg['receiver']
            data['user_id']  = msg['user_id']
            data['category_name'] = msg['category_name']
            data['category_id'] = msg['category_id']
            data['label'] = msg['label']
            data['scheduler'] = msg['scheduler']
            data['domain'] = msg['domain'];
            if 'netease' in msg:
                data['netease'] = True

            params = urllib.urlencode(data)
            response = yield http_client.fetch('http://%s/message?%s' % (msg['outbound'], params), \
                    method='POST', body=msg['rfc822Content'], request_timeout=HTTP_REQUEST_TIMEOUT, connect_timeout=HTTP_CONNECT_TIMEOUT)
        #except HttpError as e:
        #    if e.code == 413 and 'Request Entity Too Large' in e.message:
        #        logger.info('email is too large')
        #        raise WorkerException("Failed to fetch message from mongo")
        except Exception as e:
            logger.info(msg['outbound'])
            logger.exception(e)
            self.suspendOutbound(msg['outbound'])
            raise gen.Return(False)

        raise gen.Return(True)
    
    @coroutine
    def suspendOutbound(self, outbound):
        http_client = AsyncHTTPClient()
        try:
            param = {}
            param['redirect'] = 'outbound'
            param['name'] = outbound
            param['message'] = 'delivery failed'
            param['type'] = 'suspend'
            param['timeout'] = 30
            logger.info("http://%s/broadcast?%s" % (SCHEDULER, urllib.urlencode(param)))
            response = yield http_client.fetch("http://%s/broadcast?%s" % (SCHEDULER, urllib.urlencode(param)), \
                    request_timeout=HTTP_REQUEST_TIMEOUT, connect_timeout=HTTP_CONNECT_TIMEOUT)
        except Exception as e:
            logger.info("suspend outbound exception")
            logger.exception(e)

    @coroutine
    def updateMailStatus(self, msg, value):
        try:
            http_client = AsyncHTTPClient()
            params = urllib.urlencode({'email_id' : msg['email_id'],  'status' : value['status'], \
                                        'type' : value['type'], 'sub_status': value['sub_status'], 'detail':value['detail']})
            yield http_client.fetch('http://%s/updateStatus?%s' % (msg['scheduler'], params))
        except Exception as e:
            logger.exception(e)
            logger.error('failed to update mail status [%s, %s]' % (msg['email_id'], value['status']))
    

    def finishMessage(self, msg):
        try:
            if msg \
                and 'email_id' in msg.keys()   \
                and 'beginTime1' in msg.keys() \
                and 'beginTime2' in msg.keys() \
                and 'beginTime3' in msg.keys() :
                now = time.time()
                fetch = msg['beginTime2'] - msg['beginTime1']
                work = msg['beginTime3'] - msg['beginTime2']
                send = now - msg['beginTime3']
                total = now - msg['beginTime1']
                flag = ''
                if fetch >= 5.0:
                    flag = '[fetch_long]'
                if work >= 5.0:
                    flag = '[work_long]'
                if send >= 5.0:
                    flag = '[send_long]'

                logger.info('%s process email[%s] [%s] %.3f %.3f %.3f %.3f' % (flag, msg['email_id'], msg['outbound'], fetch, work, send, total))

                if 'node' in msg and msg['node'] != None:
                    msg['node'].destroy()
        except Exception as e:
            logger.exception(e)
        finally:
            if msg is not None and 'email_id' in msg:
                del self.concurrentJobs[msg['email_id']]

    @coroutine
    def processNextMessage(self):
        try:
            beginTime = time.time()
            msg = yield self.fetchMsg()
            
            if msg is None:
                self.idle = True
                return
            
            msg['beginTime1'] = beginTime
            msg['beginTime2'] = time.time()
            self.concurrentJobs[msg['email_id']] = msg['beginTime2'] 

            try:
                syslog.syslog('&WORKERIN,%.3f,%s,%s,%s,%s,%s,%s#' % (time.time(), 0, \
                    msg['email_id'], msg['user_id'], msg['category_id'], 0, msg['receiver'])) 
            except Exception as e:
                logger.fatal("write syslog error,%s,%s,%s" % (msg['email_id'], msg['user_id'], msg['category_id']))
                raise WorkerException(error_message[11])

            logger.info("IN,%s" % msg['email_id'])

            self.idle = False

            beginTime = time.time()
            for filter in self.filters:
                yield filter.apply(msg)
            
            beginTime = time.time()
            if 'mongo_name' not in msg:
                msg['mongo_name'] = DEFAULT_MONGO
            data = yield mongo.fetchMsgContent(msg['mongo_name'], msg['db'], msg['coll_name'], msg['_id'])
            if data == None or 'content' not in data:
                logger.fatal(error_message[0])
                raise WorkerException(error_message[0])
            
            syslog.syslog("&FETCH_ONE_EMAIL_TIME, %s, %s, %.3f#" % (msg['email_id'], 0, time.time() - beginTime))

            msg['content'] = data['content']
            msg['x_smtpapi'] = data['x_smtpapi']
            msg['task_id'] = data['task_id']
            
            beginTime = time.time()
            parseMessage(msg) 
            syslog.syslog("&PARSE_ONE_EMAIL, %s, %s, %.3f, %s#" % (msg['email_id'], len(msg['content']), time.time() - beginTime, 0))

            assembler = MessageAssembler()

            beginTime = time.time()
            yield assembler.run(msg)


            beginTime = time.time() 
            msg['beginTime3'] = beginTime
            success = yield self.sendToOutbound(msg)
            #if outbound is not reachable, abandon this mail
            if success:
                syslog.syslog("&TO_RELAY_TIME, %s, %s, %.3f, %s#" % (msg['email_id'], len(msg['content']), time.time() - beginTime, 0))
                syslog.syslog("&WORKEROUT,%.3f,%s,%s,%s,%s,%s#" % (time.time(), 1, 
                    msg['email_id'], msg['user_id'], msg['category_id'], msg['outbound']))
        except WorkerException as e:
            logger.warn(str(e))

            try:
                value = {'status':str(e), 'type':'WORKERERROR', \
                        'sub_status':error_message_code[str(e)],'detail':base64.standard_b64encode(str(e))}
                value_str = json.dumps(value)
                Redis.instance().updateStatus(msg['email_id'], value_str)
                yield self.updateMailStatus(msg,value)
            except Exception as e:
                logger.exception(e)

            ts = msg['email_id'].split("_")[0]
            syslog.syslog("&WORKERERROR,%s,%s,%s,%s,%s,%s, %s#" % \
                  (ts, 4, msg['email_id'], msg['user_id'], msg['category_id'], \
                  msg['label'], str(e)))

        except FakeSuccess as e:
            try:
                value = {'status':'successfully delivered', 'type':'OUT', \
                        'sub_status':'','detail':base64.standard_b64encode('successfully delivered')}
                value_str = json.dumps(value)
                Redis.instance().updateStatus(msg['email_id'], value_str)
                yield self.updateMailStatus(msg,value)
            except Exception as e:
                logger.exception(e)
            logger.info("Fake Success,%s",msg['email_id'])

        except Exception as e:
            logger.fatal("unexpected exception")
            logger.exception(e)
        finally:
            self.finishMessage(msg)

