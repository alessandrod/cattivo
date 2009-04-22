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

from ConfigParser import NoSectionError, NoOptionError
import time

from twisted.internet import defer
from twisted.web.client import getPage

try:
    import simplejson as json
except ImportError:
    import json

from cattivo.log.loggable import Loggable
from cattivo.log import log
from cattivo.utils import HOUR, SECOND, MINUTE
import cattivo


class ClientList(Loggable):
    default_request_pattern = "/client/%s"

    def __init__(self):
        Loggable.__init__(self)

    def initialize(self):
        return defer.succeed(True)

    def getClient(self, client_id):
        server = cattivo.config.get("clientlist", "host")
        try:
            request_pattern = cattivo.config.get("clientlist", "request-pattern")
        except (NoSectionError, NoOptionError):
            request_pattern = self.default_request_pattern

        request = request_pattern % client_id[0]
        url =  "%s/%s" % (server, request)
        dfr = getPage(url)
        dfr.addCallback(self._downloadPageCb)

        return dfr

    def _downloadPageCb(self, page):
        obj = json.loads(page)
        return defer.succeed(obj)

    def getClientList(self):
        return defer.succeed([])
