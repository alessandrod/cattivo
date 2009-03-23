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

from cattivo.firewall.iptables.iptables import IPTablesFirewall 
from cattivo.holes import Holes, Hole, HoleError
from cattivo.log.loggable import Loggable
from cattivo.log.log import getFailureMessage

class Firewall(Loggable):
    def __init__(self, bouncer_address, bouncer_port, clientList):
        Loggable.__init__(self)
        self.clientList = clientList
        self.systemFirewall = IPTablesFirewall(bouncer_address, bouncer_port)
        self.holes = Holes(self.systemFirewall)

    def initialize(self):
        self.holes.removeAll()
        dfr = self.systemFirewall.initialize()
        dfr.addCallback(self._systemFirewallInitializeCb)

        return dfr

    def _systemFirewallInitializeCb(self, result):
        dfr = self.clientList.getClientList()
        dfr.addCallback(self._getClientListCb)

        return dfr

    def _getClientListCb(self, client_list):
        for client_status in client_list:
            self._addClientHole(client_status)

        return defer.succeed(True)

    def clientAllowed(self, client_id):
        self.debug("checking if %s is allowed" % str(client_id))

        try:
            hole = self.holes.find(client_id)
            return defer.succeed(True)
        except HoleError:
            pass
        else:
            # this should NEVER happen
            self.warning("existing hole for %s isn't really working"
                    % str(client_id))
            return defer.succeed(False)

        dfr = self.clientList.getClient(client_id)
        dfr.addCallback(self._getClientCb)
        dfr.addErrback(self._getClientEb)

        return dfr

    def _addClientHole(self, client_status):
        client_id = client_status['client_id']
        login_time = client_status['login_time']
        expiration = client_status['expiration']
        time_left = expiration - (self.holes.now() - login_time)
        hole = Hole(client_id, time_left)
        self.holes.add(hole) 

    def _getClientCb(self, client_status):
        self._addClientHole(client_status)

        return defer.succeed(True)
    
    def _getClientEb(self, failure):
        self.warning("get client failed: %s " % getFailureMessage(failure))

        return defer.succeed(False)

