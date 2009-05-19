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

#from twisted.pair.ip import IPProtocol
from twisted.pair.ip import IPProtocol
from twisted.internet.protocol import Protocol
from twisted.internet.address import IPv4Address
from zope.interface import implements
from twisted.pair.raw import IRawDatagramProtocol
from twisted.web.http import Request, HTTPChannel
from twisted.python.reflect import namedAny

import cattivo
from cattivo.firewall.iptables.nflog.server import NFLogServer

class LoggedTransport(object):
    disconnecting = False

    def __init__(self, host, peer):
        self.host = host
        self.peer = peer

    def getPeer(self):
        return self.peer

    def getHost(self):
        return self.host

class LoggedRequest(Request):
    def requestReceived(self, command, path, version):
        Request.requestReceived(self, command, path, version)

        p = self.channel

        source = self.channel.transport.getPeer()
        destination = self.channel.transport.getHost()
        client_id = (source.host, source.port)
        p.nflogServer.logClient.logHTTP(client_id, destination.host,
                destination.port, self.getHost().host, path)


class LoggedChannel(HTTPChannel):
    requestFactory = LoggedRequest

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

        data = "".join(chr(i) for i in data[data_offset:])
        peer = IPv4Address("TCP", source, 0)
        host = IPv4Address("TCP", dest, 80)
        transport = LoggedTransport(host, peer)
        protocol = LoggedChannel()
        protocol.makeConnection(transport)
        protocol.destination = dest
        protocol.port = 80
        protocol.nflogServer = self.nflogServer
        protocol.loggerProtocol = self
        protocol.dataReceived(data)

class NFLogLoggerIPProtocol(IPProtocol):
    def __init__(self, server):
        IPProtocol.__init__(self)
        protocol = NFLogLoggerProtocol()
        protocol.nflogServer = server
        # 6 = TCP
        self.addProto(6, protocol)

class NFLogLoggerServer(NFLogServer):
    protocolClass = NFLogLoggerIPProtocol

    def __init__(self, group=0, reactor=None):
        protocol = self.protocolClass(self)
        self.logClient = self.createLogClient()
        NFLogServer.__init__(self, protocol, group, reactor=reactor)

    def createLogClient(self):
        type_name = cattivo.config.get("logger", "type")
        logger_type = namedAny(type_name)
        host = cattivo.config.get("logger", "host")

        logger = logger_type()
        return logger

import sys
if "twistd" in sys.argv[0]:
    from twisted.application.service import Application

    application = Application("TestNFLogLoggerServer")
    import time; time.sleep(2)
    server = NFLogLoggerServer(group=2)
    server.setServiceParent(application)
