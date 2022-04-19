#! /usr/bin/python
# -*- coding: utf-8 -*-

# Convenience wrapper to run Vinay Sajip's logger recipe with customisable
# console  output in each module
#
__author__  = 'Vinay Sajip <vinay_sajip at red-dove dot com> & James Parrott'
__license__ = 'Python Software Foundation 2.7.18'   #https://docs.python.org/2.7/license.html
__version__ = '0.02'

import sys, os, logging

if __name__=='__main__':
    sys.path += [os.path.join(sys.path[0], '..')]
else:
    pass
    #print "Import attempted of wrapper_logging"


#if 'metas' not in globals():
#    print "metas not found wrapper_logging.  "
#    from config import metas
#    from options_manager import makeNestedNamedTuple
#    metas = makeNestedNamedTuple( metas, 'Metas' )

#if 'options' not in globals():
#    #print "options not found in wrapper_logging.  "
#    from config import options
#    if isinstance(options,dict):
#        from options_manager import makeNestedNamedTuple
#        options = makeNestedNamedTuple( options, 'Options','' )


#print "Main body of wrapper_logging..."

#def new_Logger(*args):
#    return logging.getLogger(__name__)

# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')


def add_custom_file_to_logger(logger
                             ,custom_file_object = None
                             ,custom_logging_level = 'INFO'
                             ):
    try:
        custom_stream=logging.StreamHandler(custom_file_object)
        custom_stream.setLevel(getattr(logging,custom_logging_level))
        custom_stream.setFormatter(formatter)
        logger.addHandler(custom_stream)
    except: 
        pass

def new_Logger(  logger_name = 'main'
                ,file_name = os.path.join(sys.path[0]
                                         ,sys.argv[0].rsplit('.')[0] + '.log'
                                         )
                ,file_logging_level = 'DEBUG'
                ,console_logging_level = 'WARNING'
                ,custom_file_object = None
                ,custom_logging_level = 'INFO'):
    # type : (str,str,str,str,str,stream,str) -> Logger
    # type(stream)=='file-like object' supporting write() and flush() methods
    #
    #
    ##################################################################
    # https://docs.python.org/2.7/howto/logging-cookbook.html#logging-cookbook
    # Logging to multiple destinations
    # set up logging to file - see previous section for more details

    file_logging_level = file_logging_level.upper()
    console_logging_level = console_logging_level.upper()
    custom_logging_level = custom_logging_level.upper()

    logging.basicConfig( level = getattr(logging, file_logging_level)
                        ,format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                        ,datefmt = '%d-%m-%y %H:%M'
                        ,filename = file_name
                        ,filemode = 'w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging,console_logging_level))
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logger=logging.getLogger(logger_name)
    logger.addHandler(console)
    if custom_file_object:            
        add_custom_file_to_logger(logger, custom_file_object, custom_logging_level)
    return logger 
    #
    #######################################################################
#print "After func def in wrapper_logging..."


def make_log_message_maker(name):
    def f(self, message, *args):
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
            self.logger.addHandler(logging.NullHandler())
        getattr(self.logger, name.lower())(message, *args)
        return message
    return f

class ClassLogger():
    pass
for name in ('debug', 'info', 'warning', 'error', 'critical'):
    setattr(ClassLogger, name, make_log_message_maker(name))


if __name__ == '__main__':
    logger=new_Logger('test','wrapper_logging_test_log','DEBUG','INFO')
    logger.info("Logger set up")

