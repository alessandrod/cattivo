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

from twisted.internet import defer, reactor
from twisted.python.urlpath import URLPath

import cattivo

class IPTablesFirewallBase(object):
    entryFactory = None
    matchFactory = None
    targetFactory = None
    tableFactory = None

    def __init__(self, bouncer_address, bouncer_port, mark=1):
        if bouncer_address == "0.0.0.0":
            bouncer_address = "127.0.0.1"
        self.bouncer_address = bouncer_address
        self.bouncer_port = bouncer_port
        self.mark = mark
        self.mangle = self.tableFactory("mangle")

    def initialize(self):
        self.clean()

        def resolveCb(result):
            self.mangle.createChain(chain="cattivo")

            entry = self._createAuthenticatorEntry(result)
            self.mangle.appendEntry(entry, chain="cattivo")

            entry = self._createLocalTrafficEntry()
            self.mangle.appendEntry(entry, chain="cattivo")

            entry = self._createDefaultTproxyEntry()
            self.mangle.appendEntry(entry, chain="cattivo")
            self.mangle.commit()

            entry = self._createJumpInCattivoEntry()
            self.mangle.appendEntry(entry, chain="PREROUTING")
            self.mangle.commit()

        authenticator = cattivo.config.get("authenticator", "host")
        url = URLPath.fromString(authenticator)
        address = url.netloc
        dfr = reactor.resolve(address)
        dfr.addCallback(resolveCb)

        return dfr

    def clean(self):
        try:
            main_entry = self._createJumpInCattivoEntry()
            self.mangle.deleteEntry(main_entry, chain="PREROUTING")
        except IPTablesError, e:
            pass

        try:
            self.mangle.flushEntries(chain="cattivo")
        except IPTablesError, e:
            pass

        try:
            self.mangle.deleteChain(chain="cattivo")
        except IPTablesError, e:
            pass

        self.mangle.commit()
        return defer.succeed(None)

    def addClient(self, client_id):
        entry = self._createClientAcceptEntry(client_id)
        self.mangle.insertEntry(1, entry, chain="cattivo")
        
        entry = self._createClientLogEntry(client_id)
        self.mangle.insertEntry(1, entry, chain="cattivo")
        self.mangle.commit()

    def removeClient(self, client_id):
        entry = self._createClientAcceptEntry(client_id)
        self.mangle.deleteEntry(entry, chain="cattivo")
        self.mangle.commit()

    # helper methods that can be mocked in tests
    def _createAuthenticatorEntry(self, address):
        match = self.matchFactory("tcp")
        target = self.targetFactory("ACCEPT")
        entry = self.entryFactory(destination=address)
        entry.addMatch(match)
        entry.setTarget(target)

        return entry

    def _createJumpInCattivoEntry(self):
        in_interface = cattivo.config.get("firewall", "in-interface") or None
        out_interface = cattivo.config.get("firewall", "out-interface") or None
        entry = self.entryFactory(in_interface=in_interface,
                out_interface=out_interface)
        target = self.targetFactory("cattivo", table=self.mangle);
        entry.setTarget(target)

        return entry

    def _createLocalTrafficEntry(self):
        target = self.targetFactory("ACCEPT")
        entry = self.entryFactory(in_interface="lo")
        entry.setTarget(target)

        return entry

    def _createDefaultTproxyEntry(self):
        match = self.matchFactory("tcp", ["--destination-port", "80"])
        target = self.targetFactory("TPROXY",
                ["--on-port", str(self.bouncer_port),
                        "--on-ip", str(self.bouncer_address),
                        "--tproxy-mark", "1"])
        entry = self.entryFactory()
        entry.addMatch(match)
        entry.setTarget(target)

        return entry

    def _createClientAcceptEntry(self, client_id):
        match = self.matchFactory("tcp")
        target = self.targetFactory("ACCEPT")
        entry = self.entryFactory(source=client_id[0])
        entry.addMatch(match)
        entry.setTarget(target)

        return entry
    
    def _createClientLogEntry(self, client_id):
        match = self.matchFactory("tcp", ["--destination-port", "8080"])
        target = self.targetFactory("NFLOG", ["--nflog-group", "2"])
        entry = self.entryFactory(source=client_id[0])
        entry.addMatch(match)
        entry.setTarget(target)

        return entry
