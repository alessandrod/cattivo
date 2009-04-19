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
try:
    import simplejson as json
except ImportError:
    import json

from twisted.internet import reactor, defer
from twisted.python.reflect import namedAny
from cattivo.firewall.firewall import Firewall
from cattivo.http.bouncer import BouncerSite
from cattivo.log.loggable import Loggable, stderrHandler
from cattivo.log import loggable
from cattivo.log import log
import cattivo

from socket import SOL_IP
IP_TRANSPARENT = 19

class Launcher(Loggable):
    def createClientList(self):
        config = self.config["clientlist"]

        clientlist_type_name = config["type"]
        clientlist_type = namedAny(clientlist_type_name)

        self.debug("creating client list")
        self.clientList = clientlist_type(str(config["host"]), config["port"])
        dfr = self.clientList.initialize()

        return dfr

    def createClientListCb(self, result):
        return self.createFirewall()

    def createFirewall(self):
        self.debug("creating firewall")
        self.firewall = Firewall(self.config["bouncer"]["bind-address"],
                self.config["bouncer"]["port"], self.clientList)
        dfr = self.firewall.initialize()
        dfr.addCallback(self.firewallInitializeCb)

        return dfr

    def firewallInitializeCb(self, result):
        return self.createBouncer()

    def createBouncer(self):
        self.debug("creating bouncer")
        self.proxy_port = reactor.listenTCP(port=self.config["bouncer"]["port"],
                factory=BouncerSite(self.firewall,
                        str(self.config["authenticator"]["redirect"])),
                        interface=str(self.config["bouncer"]["bind-address"]))

        # set IP_TRANSPARENT for TPROXY to work
        self.proxy_port.socket.setsockopt(SOL_IP, IP_TRANSPARENT, 1)

        self.info("bouncer good to go")

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

    def startUnchecked(self):
        loggable.init()

        dfr = self.createClientList()
        dfr.addCallback(self.createClientListCb)

        return dfr

    def startError(self, failure):
        reactor.stop()
        failure.raiseException()

    def loadConfig(self, config_file):
        config = json.load(file(config_file))
        # FIXME: do sanity checks
        return config

    def main(self):
        self.option_parser = self.create_option_parser()
        self.options, self.args = self.option_parser.parse_args()

        try:
            self.config = cattivo.config = self.loadConfig(self.options.config_file)
        except IOError, e:
            self.option_parser.error(str(e))
            return 1

        reactor.callWhenRunning(self.start)
        reactor.run()
