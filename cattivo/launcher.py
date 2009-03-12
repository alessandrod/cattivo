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

from optparse import OptionParser
import os
import sys

from twisted.internet import reactor, defer
from cattivo.firewall.firewall import Firewall
from cattivo.http.bouncer import BouncerSite
from cattivo.client_list import ClientList
from cattivo.log.loggable import Loggable, stderrHandler
from cattivo.log import log

class Launcher(Loggable):
    def createClientList(self):
        self.clientList = ClientList()
        dfr = self.clientList.initialize()

        return dfr

    def createClientListCb(self, result):
        return self.createFirewall()

    def createFirewall(self):
        self.firewall = Firewall(self.options.iptables_chain, self.clientList)
        dfr = self.firewall.initialize()
        dfr.addCallback(self.firewallInitializeCb)

        return dfr

    def firewallInitializeCb(self, result):
        return self.createBouncer()

    def createBouncer(self):
        self.proxy_port = reactor.listenTCP(self.options.local_server_port,
                BouncerSite(self.firewall, self.options.auth_server))
    
    def create_option_parser(self):
        parser = OptionParser()
        parser.add_option('--auth-server', type='string')
        parser.add_option('--auth-server-port', type='int', default=80)
        parser.add_option('--local-server', type='string')
        parser.add_option('--local-server-port', type='int', default=80)
        parser.add_option('--iptables-chain', type='string')
        parser.add_option('--debug', type='string', action='append')
        parser.add_option('--debug-file', type='string')

        return parser
    
    def start(self):
        try:
            dfr = self.startUnchecked()
        except:
            return self.startError(defer.fail())

        dfr.addErrback(self.startError)

    def startUnchecked(self):
        log.init('CATTIVO_DEBUG', enableColorOutput=True)
        log.removeLimitedLogHandler(log.stderrHandler)
        log.addLimitedLogHandler(stderrHandler)

        if self.options.debug:
            log.setDebug(",".join(self.options.debug))

        if self.options.debug_file:
            log.outputToFiles(stderr=self.options.debug_file)

        log.logTwisted()
        self.log('starting')

        dfr = self.createClientList()
        dfr.addCallback(self.createClientListCb)

        return dfr
    
    def startError(self, failure):
        reactor.stop()
        failure.raiseException()
    
    def main(self):
        self.option_parser = self.create_option_parser()
        self.options, self.args = self.option_parser.parse_args()

        if not self.options.auth_server:
            self.option_parser.error('no auth server specified')
            return 1

        reactor.callWhenRunning(self.start)
        reactor.run()
