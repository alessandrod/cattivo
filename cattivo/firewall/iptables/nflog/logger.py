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

from twisted.pair.ip import IPProtocol
from twisted.internet.protocol import Protocol
from zope.interface import implements
from twisted.pair.raw import IRawDatagramProtocol

from cattivo.firewall.iptables.nflog.server import NFLogServer


class NFLogLoggerProtocol(Protocol):
    implements(IRawDatagramProtocol)

    def datagramReceived(self, data, partial, source, dest, protocol, version,
            ihl, tos, tot_len, fragment_id, fragment_offset, dont_fragment,
            more_fragments, ttl):
        if len(data) < 20:
            # eeeh?
            return

        data_offset = data[12] >> 2
        if data_offset > len(data):
            # whaaat?
            return

        if data_offset == len(data):
            # no data
            return

        print "DATA", "".join(chr(i) for i in data[data_offset:])

class NFLogLoggerIPProtocol(IPProtocol):
    def __init__(self):
        IPProtocol.__init__(self)
        protocol = NFLogLoggerProtocol()
        # 6 = TCP
        self.addProto(6, protocol)

class NFLogLoggerServer(NFLogServer):
    protocolClass = NFLogLoggerIPProtocol

    def __init__(self, group=0, reactor=None):
        protocol = self.protocolClass()
        NFLogServer.__init__(self, protocol, group, reactor=reactor)

import sys
if "twistd" in sys.argv[0]:
    from twisted.application.service import Application

    application = Application("TestNFLogLoggerServer")
    import time; time.sleep(2)
    server = NFLogLoggerServer(group=2)
    server.setServiceParent(application)
