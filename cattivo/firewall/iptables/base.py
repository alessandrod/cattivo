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

        self.mangle.createChain(chain="cattivo")

        entry = self._createLocalTrafficEntry()
        self.mangle.appendEntry(entry, chain="cattivo")

        #entry = self._createMarkEntry()
        #self.mangle.appendEntry(entry, chain="cattivo")

        entry = self._createDefaultTproxyEntry()
        self.mangle.appendEntry(entry, chain="cattivo")

        main_entry = self._createJumpInCattivoEntry()
        self.mangle.appendEntry(main_entry, chain="PREROUTING")
        self.mangle.commit()

        return defer.succeed(None)

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
        self.mangle.commit()

    def removeClient(self, client_id):
        entry = self._createClientAcceptEntry(client_id)
        self.mangle.deleteEntry(entry, chain="cattivo")
        self.mangle.commit()

    # helper methods that can be mocked in tests
    def _createJumpInCattivoEntry(self):
        conf = getattr(cattivo, "config", {}).get("firewall", {})
        in_interface = conf.get("in-interface", None) or None
        out_interface = conf.get("out-interface", None) or None
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

    def _createMarkEntry(self):
        tcp_match = self.matchFactory("tcp")
        socket_match = self.matchFactory("socket")
        target = self.targetFactory("MARK", ["--set-mark", str(self.mark)])
        entry = self.entryFactory()
        entry.addMatch(tcp_match)
        entry.addMatch(socket_match)
        entry.setTarget(target)

        return entry

    def _createDefaultTproxyEntry(self):
        match = self.matchFactory("tcp", ["--destination-port", "80"])
        target = self.targetFactory("TPROXY",
                ["--on-ipASD", str(self.bouncer_address),
                        "--on-port", str(self.bouncer_port),
                        "--tproxy-mark", str(self.mark), "--on-ip",
                        str(self.bouncer_address)])
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

