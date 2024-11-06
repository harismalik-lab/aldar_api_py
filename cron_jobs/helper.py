import errno
import os
import types
from logging import NOTSET, Formatter, getLogger
from logging.handlers import TimedRotatingFileHandler


def get_logger(directory='', filename='', name='', logging_level=NOTSET):
    if not directory:
        directory = os.getcwd()
    if not os.path.exists(directory):
        os.makedirs(directory)
    log_file_name = os.path.join(directory, filename)
    logging_level = logging_level
    # set TimedRotatingFileHandler for root
    formatter = Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    # use very short interval for this example, typical 'when' would be 'midnight' and no explicit interval
    handler = TimedRotatingFileHandler(log_file_name, when='midnight', backupCount=10, encoding='utf-8')
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)
    logger = getLogger(name)  # or pass string to give it a name
    logger.addHandler(handler)
    logger.setLevel(logging_level)
    return logger


def from_pyfile(filename, silent=False):
    """Updates the values in the config from a Python file.  This function
    behaves as if the file was imported as module with the
    :meth:`from_object` function.

    :param filename: the filename of the config.  This can either be an
                     absolute filename or a filename relative to the
                     root path.
    :param silent: set to ``True`` if you want silent failure for missing
                   files.

    .. versionadded:: 0.7
       `silent` parameter.
    """
    d = types.ModuleType('config')
    d.__file__ = filename
    try:
        with open(filename, mode='rb') as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if silent and e.errno in (
                errno.ENOENT, errno.EISDIR, errno.ENOTDIR
        ):
            return False
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise
    return d
