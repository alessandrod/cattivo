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
from twisted.internet.main import CONNECTION_LOST, CONNECTION_DONE
from twisted.application.service import Application, Service

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
        print "LOG", nfmsg, nfdata

        return 0


class NFLogService(Service):
    def __init__(self, group=0):
        # Service has no init
        # Service.__init__(self)
        self.nflogDescriptor = NFLogDescriptor(group)

    def startService(self):
        Service.startService(self)
        self.nflogDescriptor.startReading()

    def stopService(self):
        self.nflogDescriptor.stopReading()
        Service.stopService(self)
        

import sys
if "twistd" in sys.argv[0]:
    application = Application("TestNFLog")
    import time; time.sleep(2)
    nflogService = NFLogService(2)
    nflogService.setServiceParent(application)
