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

from ConfigParser import RawConfigParser
from optparse import OptionParser
import os
import sys

import twisted
from twisted.python.util import sibpath
from twisted.internet import reactor, defer, task
from twisted.python.reflect import namedAny
from cattivo.bouncer.http import BouncerSite
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

        self.clientList = clientlist_type()
        dfr = self.clientList.initialize()

        return dfr

    def createFirewall(self):
        from cattivo.firewall.firewall import Firewall
        
        address = cattivo.config.get("bouncer", "bind-address")
        port = cattivo.config.getint("bouncer", "port")
        self.firewall = Firewall(address, port, self.clientList)
        dfr = self.firewall.initialize()
        dfr.addCallback(self.firewallInitializeCb)

        return dfr
    
    def createLogger(self):
        from cattivo.firewall.iptables.nflog.logger import NFLogLoggerServer
        
        group = cattivo.config.getint("firewall", "log-group")
        self.logServer = NFLogLoggerServer(group)
        self.logServer.startService()
        reactor.addSystemEventTrigger("after", "shutdown",
                    self.logServer.stopService)

        return defer.succeed(None)

    def firewallInitializeCb(self, result):
        reactor.addSystemEventTrigger("after", "shutdown", self.stopFirewall)

    def stopFirewall(self):
        return self.firewall.clean()

    def createBouncer(self):
        self.bouncer_port = reactor.listenTCP(port=cattivo.config.getint("bouncer", "port"),
                factory=BouncerSite(self.firewall,
                        cattivo.config.get("authenticator", "host")),
                        interface=cattivo.config.get("bouncer", "bind-address"))

        # set IP_TRANSPARENT for TPROXY to work
        self.bouncer_port.socket.setsockopt(SOL_IP, IP_TRANSPARENT, 1)
    
        return defer.succeed(None)

    def createClientlistServer(self):
        type_name = cattivo.config.get("clientlist-server", "type")
        clientlist_server_type = namedAny(type_name)
        port = cattivo.config.getint("clientlist-server", "port")
        address = cattivo.config.get("clientlist-server", "bind-address")
        self.clientlist_server_port = reactor.listenTCP(port=port,
                factory=clientlist_server_type(), interface=address)
    
        return defer.succeed(None)

    def createLogServer(self):
        type_name = cattivo.config.get("logger-server", "type")
        log_server_type = namedAny(type_name)
        port = cattivo.config.getint("logger-server", "port")
        address = cattivo.config.get("logger-server", "bind-address")
        self.log_server_port = reactor.listenTCP(port=port,
                factory=log_server_type(), interface=address)
    
        return defer.succeed(None)

    def create_option_parser(self):
        parser = OptionParser()
        parser.add_option('--config-file', type='string', default="cattivo.conf")
        parser.add_option('--debug', type='string', action='append')
        parser.add_option('--debug-file', type='string')
        parser.add_option("--clientlist-server",
                action="store_true", default=False)
        parser.add_option("--logger-server",
                action="store_true", default=False)

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

        self.ensureTwistedPair()
        dfr = task.coiterate(self.iterateStart())
        return dfr

    def ensureTwistedPair(self):
        try:
            import twisted.pair
        except ImportError:
            import new
            m = new.module("twisted.pair")
            sys.modules["twisted.pair"] = m
            global twisted
            twisted.pair = m
            m.__file__ = os.path.join(sibpath(__file__, "twisted_pair"), "__init__.pyc")
            m.__path__ = [sibpath(__file__, "twisted_pair")]

    def logServiceStartCb(self, result, service):
        self.info("%s created successfully" % service)

        return result

    def logServiceStartEb(self, failure, service):
        self.warning("failure creating service %s: %s" % (service,
                getFailureMessage(failure)))

        return failure

    def startServiceLogged(self, name, method, *args, **kw):
        self.info("starting service %s" % name)
        dfr = method(*args, **kw)
        dfr.addCallback(self.logServiceStartCb, name)
        dfr.addErrback(self.logServiceStartEb, name)

        return dfr

    def iterateStart(self):
        yield self.startServiceLogged("clientlist", self.createClientList)
        yield self.startServiceLogged("firewall", self.createFirewall)
        yield self.startServiceLogged("logger", self.createLogger)
        yield self.startServiceLogged("bouncer", self.createBouncer)
        if self.options.clientlist_server:
            yield self.startServiceLogged("clientlist-server",
                    self.createClientlistServer)

        if self.options.logger_server:
            yield self.startServiceLogged("logger-server",
                    self.createLogServer)

    def startError(self, failure):
        reactor.stop()
        failure.raiseException()

    def loadConfig(self, config_file):
        config = RawConfigParser()
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
