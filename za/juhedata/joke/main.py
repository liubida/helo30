import sys
import os
import time
#import netutils
import conf
from logger import * 
import tornado.ioloop
import signal
#from resume import resumeJobs
#from resume_mq import resumeMessages
from tornado.ioloop import IOLoop
import tornado.httpserver
from tornado.options import define, options
#from application import Worker
from server import WebPortal
from daemon import Daemon

class Application:
    def start(self, ip, port):
        self.server = tornado.httpserver.HTTPServer(WebPortal()) 
        self.server.listen(port, address=ip)

        IOLoop.instance().start()
        
    def stop(self):
        self.server.stop()    

app = Application()

class DaemonWrapper(Daemon):
    def __init__(self, instance):
        self.prefix = './instances/%s' % instance

        self.sigterm = False

        pidfile = self.prefix + os.sep + 'worker.pid'
        stderr = self.prefix + os.sep + 'worker.err'
        Daemon.__init__(self, pidfile, stderr=stderr)

    def run(self):
        global app

        initLogger(self.prefix)
        signal.signal(signal.SIGTERM, self.exit)
        app.start(conf.IP, conf.PORT)

    def exit(self, signum = None, frame = None):
        if self.sigterm:
            return
        self.sigterm = True
        #tornado.ioloop.IOLoop.instance().add_callback(self.shutdown)
        logger.info('stopping http server')

        global app
        app.stop()

        io_loop = tornado.ioloop.IOLoop.instance()
        io_loop.add_callback(io_loop.stop)
    
    #def shutdown(self):
    #    global app
    #    logger.info('stopping http server')
    #    app.stop() 
    #    io_loop = tornado.ioloop.IOLoop.instance()

    #    deadline = time.time() + 5 
    # 
    #    def stop_loop():
    #        now = time.time()
    #        if now < deadline and (io_loop._callbacks):
    #            io_loop.add_timeout(now + 1, stop_loop)
    #        else:
    #            io_loop.stop()
    #            logger.info('worker shutdown')

    #    stop_loop()

    def do(self, action):
        if action in ('stop', 'restart'):
            self.stop()
        
        if action in ('start', 'restart'):
            if not os.path.exists(self.prefix):
                os.makedirs(self.prefix)
            self.start()

if __name__ == '__main__':
    action = sys.argv[1]
    instance = sys.argv[2]
    wrapper = DaemonWrapper(instance)
    wrapper.do(action)

