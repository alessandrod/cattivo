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
from cattivo.clientlist.db import clients

try:
    import simplejson as json
except ImportError:
    import json


not_authenticated_template = {"expiration": 0, "login_time": 0}
import time
clients["192.168.187.1"] = {"login_time": time.time(),
        "expiration": 1000000000000, "client_id": ("192.168.187.1", 0)}

def not_authenticated(client_id):
    dikt = dict(not_authenticated_template)
    dikt["client_id"] = client_id

    return dikt

class ClientResource(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        Loggable.__init__(self)

    def getChild(self, path, request):
        return self

    def render_GET(self, request):
        client_id = request.prepath[-1]
        
        try:
            dikt = clients[client_id]
        except KeyError:
            dikt = not_authenticated(client_id)

        return json.dumps(dikt)

class ClientListServerResource(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        Loggable.__init__(self)

        self.putChild("client", ClientResource())

class ClientListServerSite(Site, Loggable):
    def __init__(self):
        Site.__init__(self, ClientListServerResource())
        Loggable.__init__(self)
