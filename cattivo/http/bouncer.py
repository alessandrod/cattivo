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
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.web.util import DeferredResource, Redirect

from cattivo.log.loggable import Loggable

good_html = """
<html>
    <head>
        <title>oh hai!</title>
    </head>
    <body>
    <a href="#" onclick="window.location.reload()">porn here <-</a>
    </body>
</html>
"""

class GoodBoy(Resource):
    def render(self, request):
        return good_html

class BouncerResource(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        Loggable.__init__(self)

    def getChild(self, path, request):
        # request.channel is HTTPChannel that is our protocol
        src_address = request.channel.transport.client
        dest = request.getRequestHostname()

        self.info("bouncer request from client_id %s destination %s path %s" %
                (str(src_address), dest, request.uri))
        
        dfr = request.site.firewall.clientAllowed(src_address)
        dfr.addCallback(self._clientAllowedCb, src_address[0], dest,
                request.uri, request.site.auth_server)

        return DeferredResource(dfr)

    def _clientAllowedCb(self, res, client_id, destination, path, auth_server):
        self.info("client_id %s allowed %s" % (client_id, res))

        if res:
            return Redirect("http://%s/%s" % (destination, path))
        else:
            return Redirect(auth_server)


class BouncerSite(Site, Loggable):
    def __init__(self, firewall, auth_server):
        Site.__init__(self, BouncerResource())
        Loggable.__init__(self)
        self.firewall = firewall
        self.auth_server = auth_server
