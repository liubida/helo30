
# -*- coding:utf8 -*-
import json
import time
import datetime
print datetime.date.today()
print time.time()

y = datetime.date.today() - datetime.timedelta(1)
print y.timetuple()
print time.mktime(y.timetuple())
print int(time.mktime(y.timetuple()))
