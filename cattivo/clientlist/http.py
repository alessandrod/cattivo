# Copyright (C) 2009 Alessandro Decina
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from twisted.internet import defer
from twisted.web.client import getPage

try:
    import simplejson as json
except ImportError:
    import json

from cattivo.log.loggable import Loggable
from cattivo.log import log
from cattivo.utils import HOUR, SECOND, MINUTE
import time

class ClientList(Loggable):
    def __init__(self, server, port=80):
        Loggable.__init__(self)
        self.server = server
        self.port = port

    def initialize(self):
        return defer.succeed(True)

    def getClient(self, client_id):
        url = "%s:%d/client/%s" % (self.server, self.port, client_id[0])
        dfr = getPage(url)
        dfr.addCallback(self._downloadPageCb)

        return dfr

    def _downloadPageCb(self, page):
        obj = json.loads(page)
        return defer.succeed(obj)

        return defer.succeed({'client_id': client_id, 'login_time': time.time(),
                'expiration': 10 * SECOND})

    def getClientList(self):
        return defer.succeed([])
