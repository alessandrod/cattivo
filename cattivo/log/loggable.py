# PiTiVi , Non-linear video editor
#
#       pitivi/log/loggable.py
#
# Copyright (c) 2009, Alessandro Decina <alessandro.decina@collabora.co.uk>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import sys
import os
import time
from twisted.python import reflect
from cattivo.log.log import safeprintf, getFormattedLevelName
from cattivo.log import log

class Loggable(object, log.Loggable):
    def __init__(self):
        self.logCategory = \
                reflect.qual(reflect.getClass(self)).replace('__main__.', '')

def stderrHandler(level, object, category, file, line, message):
    """
    A log handler that writes to stderr.

    @type level:    string
    @type object:   string (or None)
    @type category: string
    @type message:  string
    """

    o = ""
    if object:
        o = '"' + object + '"'

    where = "(%s:%d)" % (file, line)

    # level   pid     object   cat      time
    # 5 + 1 + 7 + 1 + 32 + 1 + 17 + 1 + 15 == 80
    safeprintf(sys.stderr, '%s [%5d] %-17s %-32s %-15s ',
               getFormattedLevelName(level), os.getpid(), o, category,
               time.strftime("%b %d %H:%M:%S"))
    safeprintf(sys.stderr, '%-4s %s %s\n', "", message, where)

    sys.stderr.flush()

log_initialized = False
def init(options=None, config=None):
    global log_initialized

    if log_initialized:
        return

    log.init('CATTIVO_DEBUG', enableColorOutput=True)
    log.removeLimitedLogHandler(log.stderrHandler)
    log.addLimitedLogHandler(stderrHandler)
    log.setPackageScrubList('cattivo', 'twisted')

    if options is not None and options.debug:
        debug = options.debug
    elif config is not None and config["debug"]["categories"]:
        debug = config["debug"]["categories"]
    else:
        debug = ""

    if not isinstance(debug, basestring):
        debug = ",".join(debug)

    if options is not None and options.debug_file:
        debug_file = options.debug_file
    elif config is not None and config["debug"]["file"]:
        debug_file = config["debug"]["file"]
    else:
        debug_file = ""

    if debug:
        log.setDebug(debug)

    if debug_file:
        log.outputToFiles(stderr=debug_file)

    log.logTwisted()

    log_initialized = True
