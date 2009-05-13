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
from cattivo.firewall.iptables.nflog.wrapper import NFLogWrapper, \
        NFLogWrapperError

class TestNFLogWrapper(SystemTestCase):
    def testWrapper(self):
        wrapper = NFLogWrapper()

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
        wrapper = NFLogWrapper()
        self.failUnlessRaises(NFLogWrapperError, wrapper.close)
        self.failUnlessRaises(NFLogWrapperError, wrapper.bindGroup, 42)
        self.failUnlessRaises(NFLogWrapperError, wrapper.catch)


class TestNFLogServiceTest(TestCase):
    pass
