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

from common import SystemTestCase
from cattivo.firewall.iptables.nflog.wrapper import NFLog, \
        NFLogError, call_nf

class TestNFLog(SystemTestCase):
    def testWrapper(self):
        wrapper = NFLog()

        # open
        self.failUnlessEqual(wrapper.nflog_handle, 0)
        self.failUnlessEqual(wrapper.nfnl_handle, 0)
        wrapper.open()
        self.failIfEqual(wrapper.nflog_handle, 0)
        self.failIfEqual(wrapper.nfnl_handle, 0)

        # bindGroup
        self.failUnlessEqual(wrapper.nflog_g_handle, 0)
        wrapper.bindGroup(42)
        self.failIfEqual(wrapper.nflog_g_handle, 0)

        # if this is non blocking, it should hang and make the test fail
        self.failUnlessRaises(OSError, wrapper.catch)

        wrapper.close()
        
        self.failUnlessEqual(wrapper.nflog_handle, 0)
        self.failUnlessEqual(wrapper.nfnl_handle, 0)
        self.failUnlessEqual(wrapper.nflog_g_handle, 0)

    def testBadState(self):
        wrapper = NFLog()
        self.failUnlessRaises(NFLogError, wrapper.close)
        self.failUnlessRaises(NFLogError, wrapper.bindGroup, 42)
        self.failUnlessRaises(NFLogError, wrapper.catch)

    def testCallNfErrno(self):
        try:
            call_nf(lambda: -1)
        except OSError, e:
            self.failUnlessEqual(e.errno, 0)
        else:
            self.fail("this shouldn't be reached")
