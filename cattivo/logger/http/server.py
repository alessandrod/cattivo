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

from urlparse import urljoin
import time

from twisted.web.server import Site
from twisted.web.resource import Resource

from cattivo.log.loggable import Loggable

try:
    import simplejson as json
except ImportError:
    import json

class LogClientResource(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        Loggable.__init__(self)

    def getChild(self, path, request):
        return self

    def render_POST(self, request):
        client_id = request.prepath[-1]
        data = request.args["data"][0]
        obj = json.loads(data)

        tm = time.ctime(obj["timestamp"])
        destination = obj["destination"]
        port = obj["port"]
        site = urljoin(obj["http_host"], obj["http_resource"])
        logRecord = "%s - (%s, %d): %s" % (tm, destination, port, site)

        self.info(logRecord)

class LoggerServerResource(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        Loggable.__init__(self)

        log = Resource()
        log.putChild("client", LogClientResource())
        self.putChild("log", log)


class LoggerServerSite(Site, Loggable):
    def __init__(self):
        Site.__init__(self, LoggerServerResource())
        Loggable.__init__(self)
