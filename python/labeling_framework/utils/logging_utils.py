import logging

class DynamicLogger:
    def __init__(self,logname,points_to=None,init_level=None):
        self.logname = logname
        # pos = self.logname.rfind('.') # it is a submodule of a package if it has a dot
        # if pos >= 0:
        #     self.logname = self.logname[pos+1::]
        logger = self.getLogger()
        if init_level is not None:
            if points_to is not None:
                raise AttributeError('You are not supposed to set a level if you are going to follow another logger')
            logger.setLevel(init_level)
        else:
            if points_to is None:
                points_to = 'base'
            self.logger_ptr = points_to
            logger.setLevel(logging.getLogger(self.logger_ptr).level)

    def getLogger(self):
        return logging.getLogger(self.logname)
    
    def __getattr__(self,name):
        logger = self.getLogger()
        if self.logger_ptr is not None and logger.level != logging.getLogger(self.logger_ptr).level:
            logger.setLevel(logging.getLogger(self.logger_ptr).level)
        return getattr(logger,name)

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)
