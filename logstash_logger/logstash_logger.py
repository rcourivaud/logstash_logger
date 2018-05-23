# -*- coding: utf-8 -*-

"""Main module."""
from logging import Logger, DEBUG, INFO, CRITICAL, ERROR, WARNING, raiseExceptions, FileHandler, StreamHandler, Formatter, basicConfig

from logstash import TCPLogstashHandler

import socket

class LogstashLogger(Logger):
    def __init__(self, logger_name,
                 file_name=None,
                 host="localhost",
                 port=5000,
                 extra=None,
                 **kwargs):
        """
        :param logger_name:
        :param file_name:
        :param host:
        :param port:
        :param extra:
        :param kwargs:
        """

        super().__init__(name=logger_name)
        if file_name is not None:
            self.addHandler(FileHandler(filename=file_name))

        self.addHandler(TCPLogstashHandler(host, port, version=1))
        self.extra = extra

        #console logging
        console_handler = StreamHandler()
        console_handler.setLevel(DEBUG)
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)
    
        #console logging checking for logstash connection success
        try:
            socket.socket().connect((host, port))
            self.info("Connection to logstash successful.")
        except (ConnectionRefusedError, socket.gaierror):
            self.log(level=ERROR, msg="Connection to logstash unsuccessful. ({0}:{1})".format(host, port))

    def decorate(self, f):
        def wrapper(*args,**kwargs):
            import datetime
            before = datetime.datetime.now()
            res = f(*args,**kwargs)
            after = datetime.datetime.now()
            execution_time = (after-before).total_seconds()
            extra = {
                    "function_name": f.__name__, 
                    "execution_time": execution_time,
                    "function_class": f.__class__,
                    }
            if args: extra.update({'function_args': args})
            if kwargs: extra.update({'function_kwargs': kwargs})
            if res: extra.update({'function_res': res})
            self.log(level=DEBUG, msg="example message", extra_decorate=extra)

            return res
        return wrapper

    def log(self, level, msg, extra_decorate=None, *args, **kwargs):
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=1)
        """
        extra_temp = {}

        if self.extra is not None: extra_temp.update(self.extra)
        if extra_decorate is not None: extra_temp.update(extra_decorate)
    
        kwargs["extra"] = extra_temp
        
        if not isinstance(level, int):
            if raiseExceptions:
                raise TypeError("level must be an integer")
            else:
                return
        if self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)
