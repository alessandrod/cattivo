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

from cattivo.utils import HOUR, SECOND, MINUTE
import time

class ClientList(object):
    def initialize(self):
        return defer.succeed(True)

    def getClient(self, client_id):
        return defer.succeed({'client_id': client_id, 'login_time': time.time(),
                'expiration': 10 * SECOND})

    def getClientList(self):
        return defer.succeed([])
