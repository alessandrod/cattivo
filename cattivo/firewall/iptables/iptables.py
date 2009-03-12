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

from cattivo.firewall.iptables.pyipt import Entry, Match, Target, Table, \
        IPTablesError

class IptablesFirewall(object):
    def __init__(self):
        self.filter = Table("filter")
        self.mangle = Table("mangle")

    def initialize(self):
        try:
            self.ipt.deleteChain("cattivo", flush=True)
        except IPTablesError:
            pass

        for table in (self.filter, self.mangle):
            table.flushEntries("cattivo")
            table.deleteChain("cattivo")
            table.createChain("cattivo")

        match = Match("tcp", ["--syn", "--destination-port", "80"])
        target = Target("TPROXY", ["--to-ip", "127.0.0.1", "--to-port", "80")
        entry = Entry()
        entry.addMatch(match)
        entry.setTarget(target)
        self.mangle.appendEntry(entry, chain="PREROUTING") 
        
        self.filter.commit()
        self.mangle.commit()

        return defer.succeed(None)

    def addClient(self, client_id):
        match = Match("tcp")
        target = Target("ACCEPT")
        entry = Entry(source=client_id[0])
        entry.addMatch(match)
        entry.setTarget(target)
        self.mangle.insertEntry(0, entry, chain="PREROUTING") 
        self.mangle.commit()

    def removeClient(self, client_id):
        match = Match("tcp")
        target = Target("ACCEPT")
        entry = Entry(source=client_id[0])
        entry.addMatch(match)
        entry.setTarget(target)
        self.mangle.deleteEntry(entry, chain="PREROUTING") 
        self.mangle.commit()
