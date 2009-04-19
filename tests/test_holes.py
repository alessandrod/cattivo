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

from twisted.trial.unittest import TestCase
from tests.common import new_client_id
from cattivo.holes import Hole, Holes, HoleEntry, HoleError, DEFAULT_EXPIRATION
from cattivo.utils import SECOND, MINUTE, HOUR

class FakeHoles(Holes):
    def __init__(self):
        Holes.__init__(self, firewall=None)
        self.test_expired = []
        self.test_now = 0

    def now(self):
        return self.test_now

    def _addFirewall(self, hole_entry):
        pass

    def _removeFirewall(self, hole_entry):
        pass


class TestHoleEntry(TestCase):
    def setUp(self):
        self.holes = FakeHoles()
        self.hole = Hole(None, 10 * SECOND)
        self.timestamp = self.holes.now()

    def testTimeLeft(self):
        e1 = HoleEntry(self.holes, self.hole, self.timestamp)
        self.failUnlessEqual(e1.timeLeft(),
                self.timestamp + self.hole.expiration)
        self.holes.test_now = 1
        self.failUnlessEqual(e1.timeLeft(),
                (self.timestamp + self.hole.expiration) - 1)
        self.holes.test_now = self.timestamp + self.hole.expiration
        self.failUnlessEqual(e1.timeLeft(), 0)
        self.holes.test_now = self.timestamp + self.hole.expiration + 10
        self.failUnlessEqual(e1.timeLeft(), -10)

    def testCmp(self):
        h0 = Hole(None, 0 * SECOND)
        h1 = Hole(None, 1 * SECOND)
        h2 = Hole(None, 2 * SECOND)
        h3 = Hole(None, 2 * SECOND)

        e0 = HoleEntry(self.holes, h0, self.timestamp)
        e1 = HoleEntry(self.holes, h1, self.timestamp)
        e2 = HoleEntry(self.holes, h2, self.timestamp)
        e3 = HoleEntry(self.holes, h3, self.timestamp)

        lst = [e0, e3, e2, e1]
        lst.sort()

        self.failUnlessEqual(lst, [e0, e1, e2, e3])


class TestHoles(TestCase):
    def setUp(self):
        self.holes = FakeHoles()

    def testNumHoles(self):
        self.failUnlessEqual(self.holes.getNumHoles(), 0)

    def testFindNoHoles(self):
        client_id = new_client_id()
        self.failUnlessRaises(HoleError, self.holes.find, client_id)

    def testCreateHole(self):
        client_id = new_client_id()
        hole = Hole(client_id)
        self.failUnlessEqual(hole.expiration, DEFAULT_EXPIRATION)

        hole = Hole(client_id, expiration=10 * SECOND)
        self.failUnlessEqual(hole.expiration, 10 * SECOND)

    def testAddRemoveHoles(self):
        client_id1 = new_client_id()
        hole1 = Hole(client_id1)
        hole1_copy = Hole(client_id1)
        # add an hole
        self.holes.add(hole1)
        # can't add twice
        self.failUnlessRaises(HoleError, self.holes.add, hole1_copy)
        self.failUnlessEqual(self.holes.getNumHoles(), 1)

        # check for existence
        tmp = self.holes.find(client_id1)
        self.failUnlessEqual(hole1.client_id, tmp.client_id)

        # remove the hole
        self.holes.remove(client_id1)
        # can't remove twice
        self.failUnlessRaises(HoleError, self.holes.remove, client_id1)
        self.failUnlessEqual(self.holes.getNumHoles(), 0)

    def testExpirationTime(self):
        self.failUnlessIdentical(self.holes.getNextExpiration(), None)

        client_id1 = new_client_id()
        hole1 = Hole(client_id1, expiration=5 * SECOND)
        self.holes.add(hole1)

        # self.holes.now() always returns 0, so the next expiration is always
        # 0 + earliest_hole.expiration

        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole1.expiration)

        client_id2 = new_client_id()
        hole2 = Hole(client_id2, expiration=10 * SECOND)
        self.holes.add(hole2)
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole1.expiration)

        client_id3 = new_client_id()
        hole3 = Hole(client_id3, expiration=1 * SECOND)
        self.holes.add(hole3)
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole3.expiration)

        now = 1
        self.holes.test_now = now
        self.holes._hole_expired_call.cancel()
        self.holes._holeExpired()
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole1.expiration - now)

        self.holes.remove(client_id1)
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole2.expiration - now)

        self.holes.remove(client_id2)
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessIdentical(next_expiration, None)

    def testExpirationTimeCatchUp(self):
        client_id1 = new_client_id()
        hole1 = Hole(client_id1, expiration=5 * SECOND)
        self.holes.add(hole1)

        client_id2 = new_client_id()
        hole2 = Hole(client_id2, expiration=10 * SECOND)
        self.holes.add(hole2)

        client_id3 = new_client_id()
        hole3 = Hole(client_id3, expiration=11 * SECOND)
        self.holes.add(hole3)

        now = 10
        self.holes.test_now = now
        self.holes._hole_expired_call.cancel()
        self.holes._holeExpired()

        next_expiration = self.holes.getNextExpiration()
        self.failUnlessEqual(next_expiration, hole3.expiration - now)

        self.holes.remove(client_id3)
        next_expiration = self.holes.getNextExpiration()
        self.failUnlessIdentical(next_expiration, None)
