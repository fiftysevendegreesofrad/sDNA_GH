#! /usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import inspect


class LoggingOptions(object):
    default_path = __file__
    working_folder = os.path.dirname(default_path)
    logger_name = 'root'
    log_file = __name__ + '.log'
    logs_dir = 'logs'
    log_file_level = 'DEBUG'
    log_console_level = 'INFO'
    #
    log_custom_level = 'INFO'
    log_fmt_str = '%(name)-12s: %(levelname)-8s %(message)s'
    log_date_fmt = '%d-%m-%y %H:%M'





# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')


def add_custom_file_to_logger(logger
                             ,custom = None
                             ,options = LoggingOptions
                             ):
    try:
        custom_stream=logging.StreamHandler(custom)
        custom_stream.setLevel(getattr(logging, options.log_custom_level))
        custom_stream.setFormatter(logging.Formatter(options.log_fmt_str))
        logger.addHandler(custom_stream)
    except: 
        pass



####################################################################################
#
# Core functionality from the python.org logging cookbook
#
def new_Logger(  options = LoggingOptions
                ,custom = None):
    # type : (type[any]/namedtuple, stream, str) -> Logger
    # stream is any'file-like object' supporting write() and flush() methods
    """ Wrapper for Vinay Sajip's logger recipe with customisable
        console output, configured via options in a class/namedtuple 
        https://docs.python.org/2.7/howto/logging-cookbook.html#logging-cookbook """


    file_name =  os.path.join(options.working_folder
                             ,options.logs_dir
                             ,options.log_file
                             )

    # ensure logging levels are in all capital letters.
    file_logging_level = options.log_file_level.upper()
    console_logging_level = options.log_console_level.upper()

    logging.basicConfig( level = getattr(logging, file_logging_level)
                       ,format = options.log_fmt_str
                       ,datefmt = options.log_date_fmt
                       ,filename = file_name
                       ,filemode = 'w'
                       )

    # define a Handler which writes to the sys.stderr
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, console_logging_level))
    
    # specify handler format
    console.setFormatter(logging.Formatter(options.log_fmt_str))
    
    # add the handler to the new_logger
    new_logger = logging.getLogger(options.logger_name)
    new_logger.addHandler(console)

    if custom:            
        add_custom_file_to_logger(new_logger, custom, options)
    return new_logger 
#
####################################################################################



####################################################################################
#
# A factory for a class with logger attributes, that add in the class of the instance's
# name (the subclass name) into the logging messages.  Uses multiple inheritance.
#
def make_self_logger(self, logger = None, module_name = '', name = None):
    if name is None:
        name = self.__class__.__name__
    if module_name:
        module_name += '.'
    if logger:
        logger = logger.getChild(name)
    else:
        logger = logging.getLogger(module_name + name)
    logger.addHandler(logging.NullHandler())
    return logger

def make_log_message_maker(method, logger = None, module_name = None):
    if module_name is None:
        module_name = __name__
    def f(self, message, *args):
        if not hasattr(self, 'logger'):
            self.logger = make_self_logger(self, logger, module_name)
        getattr(self.logger, method)(message, *args)
        return message
    return f

def add_methods_decorator(obj, methods = None, method_maker = make_log_message_maker, **kwargs):
    if methods is None:
        methods = ('debug', 'info', 'warning', 'error', 'critical', 'exception')
    for method in methods:
        setattr(obj, method, method_maker(method, **kwargs))

def class_logger_factory(logger = None, module_name = None):
    """ Factory for ClassLogger Classes.  Otherwise __name__ will 
        be 'wrapper.logging' now matter which module they were instantiated
        in.  """
    class ClassLogger(object):
        """ Class to inherit a class logger from, e.g. via co-operative 
            multiple inheritance (CMI).  After instantiation, .SubClassName is
            appended to module_name in its logs, e.g. to aid debugging.  
            
            To add in a class logger via 
            composition instead of inheritance, assign the attribute directly 
            to make_self_logger() with the desired name as an argument"""
        pass
    add_methods_decorator(ClassLogger, logger = logger, module_name = module_name)
    return ClassLogger
#
#
####################################################################################



####################################################################################
#
# A single callable wrapper with a cache.  Saves logging messages from before the
# logger system is setup until they can be flushed into the logger, and provides
# a central point to redirect all log messaging calls through, (e.g. if the logger
# itself needs debugging, providing the perfect place to temporarily use print)
#
#
class Output(object): 
    """   Wrapper class for logger, logging, print, with a cache.  Example setup:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    cache = []
    output = Output(cache, logger)
    """
    def set_logger(self, logger, flush = True):
        self.logger = logger
        if flush and self.tmp_logs:
            self.flush()

    def __init__(self
                ,tmp_logs = None
                ,logger = None
                ):
        if not isinstance(tmp_logs, list): #assert not isinstance(None, list)
            tmp_logs = []
        self.tmp_logs = tmp_logs
        if logger is not None:
            self.set_logger(logger, flush = False)



    def store(self, message, logging_level):
        self.tmp_logs.append( (message, logging_level) )

    def __call__(self, message, logging_level = "INFO", logging_dict = {}):
        #type: (str, str, dict, list) -> str
        
        #print(message)

        if logging_dict == {} and hasattr(self, 'logger'): 
            logging_dict = dict( DEBUG = self.logger.debug
                                ,INFO = self.logger.info
                                ,WARNING = self.logger.warning
                                ,ERROR = self.logger.error
                                ,CRITICAL = self.logger.critical
                                )

        logging_level = logging_level.upper()
        if logging_level in logging_dict:
            logging_dict[logging_level](message)
        else:
            self.store(message, logging_level)

        return logging_level + ' : ' + message + ' '

    def flush(self):
        tmp_logs = self.tmp_logs[:] # __call__ might cache back to tmp_logs
        self.tmp_logs[:] = [] # Mutate list initialised with
        for tmp_log_message, tmp_log_level in tmp_logs:
            self.__call__(tmp_log_message, tmp_log_level)
#
#
#
##############################################################################
#
# Supplements an instance of the above Class by adding in the names found
# for a variable
# to a debug message (as well as its value) just by calling:.
#
#  debug(variable)
#
# Python 3 only, to get in inspect.currentframe() to work as intended
#
#
class Debugger(object):
    """ Wrapper class for quick debugging messages that prepends a variable's 
    name (if it can be found) to its value, then calls an output callable.  
    Example setup:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    cache = []
    output = Output(cache, logger)
    debug = Debugger(output)
    """
    def __init__(self, output = None):
        #type(type[any], function) -> None  # callable object
        if output is None:
            output = Output()
        self.output = output # want to call an instance that we also use for
                             # higher logging level messages so 
                             # composition instead of inheritance is used
    def __call__(self, x):
        c = inspect.currentframe().f_back.f_locals.items()

        names = [name.strip("'") for name, val in c if val is x]
        # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
        # https://stackoverflow.com/a/40536047

        if names:
            return self.output(str(names) + ' == ' + str(x)+' ','DEBUG')
        else:
            return self.output(str(x)+' ','DEBUG')
#
#
##############################################################################
