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

from twisted.internet import reactor
from bisect import insort_right
import time

from cattivo.log.loggable import Loggable
from cattivo.log.log import getFailureMessage
from cattivo.utils import MINUTE

DEFAULT_EXPIRATION = 60 * MINUTE

class HoleError(Exception):
    pass

class Hole(object):
    def __init__(self, client_id, expiration=DEFAULT_EXPIRATION):
        self.client_id = client_id
        self.expiration = expiration

class HoleEntry(object):
    def __init__(self, holes, hole, timestamp):
        self.holes = holes
        self.hole = hole
        self.timestamp = timestamp

    def timeLeft(self):
        abs = self.timestamp + self.hole.expiration
        return abs - self.holes.now()

    def __cmp__(self, other):
        if not isinstance(other, HoleEntry):
            raise TypeError("wtf?")

        left = self.timeLeft()
        other_left = other.timeLeft()

        return cmp(left, other_left)

class Holes(Loggable):
    def __init__(self, firewall):
        Loggable.__init__(self)
        self._firewall = firewall
        self._hole_entries =  {}
        self._hole_entries_by_expiration = []
        self._hole_expired_call = None

    def add(self, hole):
        if hole.client_id in self._hole_entries:
            raise HoleError()

        now = self.now()
        hole_entry = HoleEntry(self, hole, now)
        self._hole_entries[hole.client_id] = hole_entry

        try:
            earliest = self._hole_entries_by_expiration[0]
        except IndexError:
            earliest = None

        self._addFirewall(hole_entry)

        insort_right(self._hole_entries_by_expiration, hole_entry)
        new_earliest = self._hole_entries_by_expiration[0]

        if earliest is None or new_earliest != earliest:
            self._rescheduleNextExpiration()

    def _rescheduleNextExpiration(self):
        if self._hole_expired_call is not None:
            self._hole_expired_call.cancel()
            self._hole_expired_call = None

        while len(self._hole_entries_by_expiration):
            hole_entry = self._hole_entries_by_expiration[0]
            timeout = hole_entry.timeLeft()
            if timeout <= 0:
                self.info("catching up")
                self._remove(hole_entry.hole.client_id)
                continue

            self._hole_expired_call = self._callLater(timeout, self._holeExpired)
            self.info("scheduled next expiration %d" % timeout)
            break

    def _callLater(self, timeout, callback, *args, **kw):
        call = reactor.callLater(timeout, callback, *args, **kw)
        return call

    def remove(self, client_id):
        need_resched = self._remove(client_id)
        if need_resched:
            self._rescheduleNextExpiration()

    def _remove(self, client_id):
        try:
            hole_entry = self._hole_entries.pop(client_id)
        except KeyError:
            raise HoleError()

        if self._hole_entries_by_expiration[0] is hole_entry:
            need_resched = True
        else:
            need_resched = False

        self.debug("removing hole entry for %s" %
                str(hole_entry.hole.client_id))
        self._hole_entries_by_expiration.remove(hole_entry)
        self._removeFirewall(hole_entry)

        return need_resched

    def removeAll(self):
        for hole_entry in self._hole_entries_by_expiration[::-1]:
            self.remove(hole_entry.hole.client_id)

    def find(self, client_id):
        try:
            return self._hole_entries[client_id].hole
        except KeyError:
            raise HoleError()

    def getNumHoles(self):
        return len(self._hole_entries)

    def getNextExpiration(self):
        try:
            return self._hole_entries_by_expiration[0].timeLeft()
        except IndexError:
            return None

    def now(self):
        return time.time()

    def _holeExpired(self):
        self.info("hole entry expired")
        self._hole_expired_call = None
        hole_entry = self._hole_entries_by_expiration[0]
        self.info("%s" % str(hole_entry.hole.client_id))
        self.remove(hole_entry.hole.client_id)

    def _addFirewall(self, hole_entry):
        self._firewall.addClient(hole_entry.hole.client_id)

    def _removeFirewall(self, hole_entry):
        self.debug("remove firewall rule for %s" %
                str(hole_entry.hole.client_id))
        self._firewall.removeClient(hole_entry.hole.client_id)
