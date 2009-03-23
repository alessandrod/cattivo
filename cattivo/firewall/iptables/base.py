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

# FIXME: this is fugly
def run_system_tests():
    import os
    return os.environ.get("CATTIVO_TEST_SYSTEM", "0") == "1"

if not run_system_tests():
    class IPTablesError(Exception):
        pass
else:
    from cattivo.firewall.iptables.pyipt import IPTablesError

class IPTablesFirewallBase(object):
    entryFactory = None
    matchFactory = None
    targetFactory = None
    tableFactory = None

    def __init__(self):
        self.mangle = self.tableFactory("mangle")

    def initialize(self):
        try:
            main_entry = self._createJumpInCattivoEntry()
            self.mangle.deleteEntry(main_entry, chain="PREROUTING")
        except IPTablesError, e:
            main_entry = None

        try:
            self.mangle.flushEntries(chain="cattivo")
        except IPTablesError, e:
            pass
            
        try:
            self.mangle.deleteChain(chain="cattivo")
        except IPTablesError, e:
            pass

        self.mangle.createChain(chain="cattivo")

        entry = self._createDefaultTproxyEntry()
        self.mangle.appendEntry(entry, chain="cattivo")
        if main_entry is None:
            main_entry = self._createJumpInCattivoEntry()
        self.mangle.appendEntry(main_entry, chain="PREROUTING") 
        self.mangle.commit()

        return defer.succeed(None)

    def addClient(self, client_id):
        entry = self._createClientAcceptEntry(client_id)
        self.mangle.insertEntry(0, entry, chain="cattivo") 
        self.mangle.commit()

    def removeClient(self, client_id):
        entry = self._createClientAcceptEntry(client_id)
        self.mangle.deleteEntry(entry, chain="cattivo") 
        self.mangle.commit()

    # helper methods that can be mocked in tests
    def _createJumpInCattivoEntry(self):
        entry = self.entryFactory()
        target = self.targetFactory("cattivo", table=self.mangle);
        entry.setTarget(target)

        return entry

    def _createDefaultTproxyEntry(self):
        match = self.matchFactory("tcp", ["--syn", "--destination-port", "80"])
        target = self.targetFactory("TPROXY", ["--to-ip", "127.0.0.1", "--to-port", "80"])
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

