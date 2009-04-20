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

from twisted.trial.unittest import TestCase

from tests.common import new_client_id, run_system_tests
from cattivo.firewall.iptables.base import IPTablesFirewallBase
import cattivo.firewall.iptables.base
from cattivo.log import loggable

loggable.init()

class IPTablesError(Exception):
    pass

cattivo.firewall.iptables.base.IPTablesError = IPTablesError

import os

if run_system_tests():
    from cattivo.firewall.iptables.pyipt import Entry, Match, Target, Table
    BaseEntry = Entry
    BaseMatch = Match
    BaseTarget = Target
    BaseTable = Table
else:
    class BaseEntry(object):
        def __init__(self, source, in_interface=None, out_interface=None):
            pass

        def setTarget(self, target):
            pass

        def addMatch(self, match):
            pass

    class BaseMatch(object):
        def __init__(self, name, arguments=None):
            pass

    class BaseTarget(object):
        def __init__(self, name, arguments=None, table=None):
            pass

    class BaseTable(object):
        def __init__(self, name):
            pass

        def appendEntry(self, *args):
            pass

        def insertEntry(self, *args):
            pass

        def deleteEntry(self, *args):
            pass

        def flushEntries(self, *args):
            pass

        def createChain(self, *args):
            pass

        def deleteChain(self, *args):
            pass

class TestEntry(BaseEntry):
    def __init__(self, source=None, in_interface=None, out_interface=None):
        BaseEntry.__init__(self, source=source)
        self.source = source
        self.target = None
        self.in_interface = in_interface
        self.out_interface = out_interface
        self.matches = []

    def setTarget(self, target):
        BaseEntry.setTarget(self, target)
        self.target = target

    def addMatch(self, match):
        BaseEntry.addMatch(self, match)
        self.matches.append(match)

class TestMatch(BaseMatch):
    def __init__(self, name, arguments=None):
        BaseMatch.__init__(self, name, arguments)
        self.name = name
        self.arguments = arguments

class TestTarget(BaseTarget):
    def __init__(self, name, arguments=None, table=None):
        BaseTarget.__init__(self, name, arguments, table)
        self.name = name
        self.arguments = arguments
        self.table = table

class TestTable(BaseTable):
    def __init__(self, name):
        BaseTable.__init__(self, name)
        self.commits = 0
        self._deleted_entries = []
        self._entries = []
        self._flush = []
        self._chains = []
        self._deleted_chains = []

    def createChain(self, chain):
        self._chains.append(chain)
        BaseTable.createChain(self, chain)

    def deleteChain(self, chain):
        self._deleted_chains.append(chain)
        BaseTable.deleteChain(self, chain)

    def flushEntries(self, chain):
        self._flush.append(chain)
        BaseTable.flushEntries(self, chain)

    def deleteEntry(self, entry, chain):
        self._deleted_entries.append((entry, chain))
        BaseTable.deleteEntry(self, entry, chain)

    def appendEntry(self, entry, chain):
        self._entries.append((entry, chain))
        BaseTable.appendEntry(self, entry, chain)

    def insertEntry(self, pos, entry, chain):
        self._entries.insert(pos, (entry, chain))
        BaseTable.insertEntry(self, pos, entry, chain)

    def commit(self):
        self.commits += 1

class FakeIPTablesFirewall(IPTablesFirewallBase):
    entryFactory = TestEntry
    matchFactory = TestMatch
    targetFactory = TestTarget
    tableFactory = TestTable

class TestIPTablesFirewall(TestCase):
    def setUp(self):
        self.firewall = FakeIPTablesFirewall('127.0.0.1', '8081')

    def testInitialize(self):
        mangle = self.firewall.mangle

        def check_initialize(result):
            # check that the main entry is removed
            if not run_system_tests():
                self.failUnlessEqual(len(mangle._deleted_entries), 1)
                entry, chain = mangle._deleted_entries[0]
                self.failUnlessEqual(entry.matches, [])
                target = entry.target
                self.failUnlessEqual(target.name, "cattivo")
                self.failUnlessIdentical(target.table, mangle)

            # cattivo table must be reinitialized
            self.failUnlessEqual(mangle._flush, ["cattivo"])
            self.failUnlessEqual(mangle._deleted_chains, ["cattivo"])
            self.failUnlessEqual(mangle._chains, ["cattivo"])

            # two entries are created at startup
            self.failUnlessEqual(len(mangle._entries), 3)

            # default TPROXY entry
            entry, chain = mangle._entries[1]
            self.failUnlessEqual(chain, "cattivo")
            self.failUnlessEqual(len(entry.matches), 1)
            match = entry.matches[0]
            self.failUnlessEqual(match.name, "tcp")
            self.failUnlessEqual(match.arguments,
                    ["--destination-port", "80"])
            target = entry.target
            self.failUnlessEqual(target.name, "TPROXY")
            self.failUnlessEqual(target.arguments,
                    ["--on-ip", "127.0.0.1", "--on-port", "8081",
                    "--tproxy-mark", "1"])

            # main entry
            entry, chain = mangle._entries[2]
            self.failUnlessEqual(chain, "PREROUTING")
            self.failUnlessEqual(len(entry.matches), 0)
            target = entry.target
            self.failUnlessEqual(target.name, "cattivo")
            self.failUnlessEqual(target.table, mangle)

            self.failUnlessEqual(mangle.commits, 2)

        self.failUnlessEqual(mangle.commits, 0)

        dfr = self.firewall.initialize()
        dfr.addCallback(check_initialize)

        return dfr

    def testAddRemoveClient(self):
        mangle = self.firewall.mangle

        def carry_on(result):
            client_id1 = new_client_id()

            self.failUnlessEqual(mangle.commits, 2)
            self.firewall.addClient(client_id1)
            self.failUnlessEqual(mangle.commits, 3)
            entry, chain = mangle._entries[1]
            self.failUnlessEqual(chain, "cattivo")
            self.failUnlessEqual(entry.source, client_id1[0])
            self.failUnlessEqual(entry.target.name, "ACCEPT")
            self.failUnlessEqual(len(entry.matches), 1)
            self.failUnlessEqual(entry.matches[0].name, "tcp")

            self.firewall.removeClient(client_id1)
            self.failUnlessEqual(mangle.commits, 4)
            entry, chain = mangle._deleted_entries[-1]
            self.failUnlessEqual(chain, "cattivo")
            self.failUnlessEqual(entry.source, client_id1[0])
            self.failUnlessEqual(entry.target.name, "ACCEPT")
            self.failUnlessEqual(len(entry.matches), 1)
            self.failUnlessEqual(entry.matches[0].name, "tcp")

        dfr = self.firewall.initialize()
        dfr.addCallback(carry_on)

        return dfr
