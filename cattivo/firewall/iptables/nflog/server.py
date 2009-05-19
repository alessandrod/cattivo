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

import errno
from socket import AF_INET

from twisted.internet.abstract import FileDescriptor
from twisted.application.internet import GenericServer
from twisted.pair.ethernet import EthernetProtocol

from cattivo.firewall.iptables.nflog.wrapper import NFLog, \
        NFULNL_COPY_PACKET

class NFLogDescriptor(FileDescriptor):
    def __init__(self, group, reactor=None):
        FileDescriptor.__init__(self, reactor)
        self.wrapper = NFLog()
        self.wrapper.open()
        self.wrapper.bindProtocolFamily(AF_INET)
        self.group = group
        self.wrapper.bindGroup(group)
        self.wrapper.setMode(NFULNL_COPY_PACKET, 0xFFFF)
        self.wrapper.setCallback(self.nflogCallback)

    def fileno(self):
        return self.wrapper.fd

    def doRead(self):
        try:
            # this will trigger our callback
            self.wrapper.catch()
        except (OSError, IOError), ioe:
            if ioe.args[0] in (errno.EAGAIN, errno.EINTR, errno.ENOBUFS):
                return
            else:
                return CONNECTION_LOST

    def nflogCallback(self, nfmsg, nfdata):
        # -1 == failure
        return 0

class NFLogPort(NFLogDescriptor):
    def __init__(self, protocol, group=0):
        NFLogDescriptor.__init__(self, group)
        self.protocol = protocol

    def startListening(self):
        self.startReading()
        self.connected = 1
        self.protocol.makeConnection(self)

    def stopListening(self):
        self.stopReading()

    def connectionLost(self, reason=None):
        NFLogDescriptor.connectionLost(self, reason)

    def nflogCallback(self, nfmsg, nfdata):
        buf = nfdata.getPayload()
        self.protocol.datagramReceived(buf)

        return 0

class NFLogFakeEthernetProtocol(EthernetProtocol):
    def __init__(self, protocol):
        EthernetProtocol.__init__(self)
        self.protocol = protocol

    def datagramReceived(self, data, partial=0):
        source = None
        dest = None
        protocol = None
        self.protocol.datagramReceived(data, partial,
                source, dest, protocol)


class NFLogServer(GenericServer):
    def __init__(self, protocol, group=0, reactor=None):
        GenericServer.__init__(self, reactor=reactor)
        ethernetProtocol = NFLogFakeEthernetProtocol(protocol)
        self.protocol = ethernetProtocol
        self.group = group

    def _getPort(self):
        port = NFLogPort(self.protocol, self.group)
        port.startListening()

        return port
