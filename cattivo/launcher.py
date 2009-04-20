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

from ConfigParser import ConfigParser
from optparse import OptionParser
import os
import sys

from twisted.internet import reactor, defer, task
from twisted.python.reflect import namedAny
from cattivo.http.bouncer import BouncerSite
from cattivo.log.loggable import Loggable
from cattivo.log import loggable
from cattivo.log.log import getFailureMessage
from cattivo.log import log
import cattivo

from socket import SOL_IP
IP_TRANSPARENT = 19

class Launcher(Loggable):
    options = None

    def createClientList(self):
        clientlist_type_name = cattivo.config.get("clientlist", "type")
        clientlist_type = namedAny(clientlist_type_name)

        host = cattivo.config.get("clientlist", "host")
        port = cattivo.config.getint("clientlist", "port")

        self.debug("creating client list")
        self.clientList = clientlist_type(host, port)
        dfr = self.clientList.initialize()

        return dfr

    def createClientListCb(self, result):
        self.log("clientlist client created successfully")

    def createClientListEb(self, failure):
        self.warning("failure creating clientlist client %s" %
                getFailureMessage(failure))

        return failure

    def createFirewall(self):
        from cattivo.firewall.firewall import Firewall
        
        self.debug("creating firewall")
        address = cattivo.config.get("bouncer", "bind-address")
        port = cattivo.config.getint("bouncer", "port")
        self.firewall = Firewall(address, port, self.clientList)
        dfr = self.firewall.initialize()
        dfr.addCallback(self.firewallInitializeCb)

        return dfr

    def firewallInitializeCb(self, result):
        reactor.addSystemEventTrigger("after", "shutdown", self.stopFirewall)

    def stopFirewall(self):
        return self.firewall.clean()

    def createFirewallCb(self, result):
        self.log("firewall created successfully")

    def createFirewallEb(self, failure):
        self.warning("failure creating firewall %s" %
                getFailureMessage(failure))

        return failure

    def createBouncer(self):
        self.debug("creating bouncer")
        self.proxy_port = reactor.listenTCP(port=cattivo.config.getint("bouncer", "port"),
                factory=BouncerSite(self.firewall,
                        cattivo.config.get("authenticator", "redirect")),
                        interface=cattivo.config.get("bouncer", "bind-address"))

        # set IP_TRANSPARENT for TPROXY to work
        self.proxy_port.socket.setsockopt(SOL_IP, IP_TRANSPARENT, 1)

        self.info("bouncer good to go")
    
        return defer.succeed(None)

    def createBouncerCb(self, result):
        self.log("bouncer created successfully")

    def createBouncerEb(self, failure):
        self.warning("failure creating bouncer %s" %
                getFailureMessage(failure))

        return failure

    def create_option_parser(self):
        parser = OptionParser()
        parser.add_option('--config-file', type='string', default="cattivo.conf")
        parser.add_option('--debug', type='string', action='append')
        parser.add_option('--debug-file', type='string')

        return parser

    def start(self):
        try:
            dfr = self.startUnchecked()
        except:
            return self.startError(defer.fail())

        dfr.addErrback(self.startError)

    def initLog(self):
        loggable.init(self.options, cattivo.config)

    def startUnchecked(self):
        loggable.init(self.options, cattivo.config)
        dfr = task.coiterate(self.iterateStart())
        return dfr

    def iterateStart(self):
        dfr = self.createClientList()
        dfr.addCallback(self.createClientListCb)
        dfr.addErrback(self.createClientListEb)
        yield dfr

        dfr = self.createFirewall()
        dfr.addCallback(self.createFirewallCb)
        dfr.addErrback(self.createFirewallEb)
        yield dfr

        dfr = self.createBouncer()
        dfr.addCallback(self.createBouncerCb)
        dfr.addErrback(self.createBouncerEb)
        yield dfr

    def startError(self, failure):
        reactor.stop()
        failure.raiseException()

    def loadConfig(self, config_file):
        config = ConfigParser()
        config.read(config_file)

        cattivo.config = config

        return config

    def main(self):
        self.option_parser = self.create_option_parser()
        self.options, self.args = self.option_parser.parse_args()

        try:
            self.loadConfig(self.options.config_file)
        except IOError, e:
            self.option_parser.error(str(e))
            return 1

        reactor.callWhenRunning(self.start)
        reactor.run()
