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

from cattivo.firewall.iptables.pyipt import Entry, Match, Target, Table, \
        IPTablesError
from cattivo.firewall.iptables.base import IPTablesFirewallBase
import cattivo.firewall.iptables.base

cattivo.firewall.iptables.base.IPTablesError = IPTablesError

class IPTablesFirewall(IPTablesFirewallBase):
    entryFactory = Entry
    matchFactory = Match
    targetFactory = Target
    tableFactory = Table
