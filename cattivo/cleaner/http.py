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

from twisted.web import http
from twisted.web.resource import NoResource
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.guard import BasicCredentialFactory, HTTPAuthSessionWrapper
from twisted.internet import defer
from twisted.cred.portal import Portal
from twisted.cred.checkers import FilePasswordDB

import cattivo
from cattivo.log.loggable import Loggable

class ResourceRemoved(Resource):
    template = """
<html>
  <head><title>Client removed</title></head>
  <body>
    <h1>Client removed</h1>
  </body>
</html>
"""

    def __init__(self):
        Resource.__init__(self)
        self.code = http.OK

    def render(self, request):
        request.setResponseCode(self.code)
        request.setHeader("content-type", "text/html")
        return self.template

class CleanerRealm(object):
    def requestAvatar(self, avatarId, mind, *interfaces):
        def logout():
            pass
        res = (interfaces[0], CleanerResourceAuthenticated(), logout)

        return defer.succeed(res)


class RemoveResource(Resource):
    def getChild(self, path, request):
        client_id = (path, 0)
        if request.site.firewall.removeClient(client_id):
            # not really an error
            return ErrorPage(http.OK, "", "")

        return NoResource()

class CleanerResourceAuthenticated(Resource):
    def __init__(self):
        Resource.__init__(self)

        self.putChild("remove", RemoveResource())


class CleanerResource(Resource, Loggable):
    def __init__(self, portal):
        Resource.__init__(self)
        Loggable.__init__(self)

        # support only basic auth for now
        credentialFactories = [BasicCredentialFactory("cattivo")]
        self.resource = HTTPAuthSessionWrapper(portal, credentialFactories)

    def getChild(self, path, request):
        # always delegate to the authenticated resource
        request.postpath.insert(0, request.prepath.pop())
        return self.resource

class CleanerSite(Site, Loggable):
    def __init__(self, firewall):
        self.user = cattivo.config.get("cleaner", "user")
        self.passwd_file = cattivo.config.get("cleaner", "passwd-file")
        checker = FilePasswordDB(self.passwd_file)
        self.realm = CleanerRealm()
        self.portal = Portal(self.realm)
        self.portal.registerChecker(checker)
        self.firewall = firewall
        Site.__init__(self, CleanerResource(self.portal))
        Loggable.__init__(self)
