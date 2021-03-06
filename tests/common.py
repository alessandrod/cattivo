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

import os

from twisted.trial.unittest import TestCase
from twisted.python.util import sibpath

from cattivo.launcher import Launcher

mac = 0
ip = 0

launcher = None
def init_tests():
    global launcher

    if launcher is not None:
        return

    launcher = Launcher()
    launcher.loadConfig(sibpath(__file__, "cattivo.conf"))
    launcher.initLog()

def new_client_id():
    global mac, ip
    m = mac
    i = ip
    mac += 1
    ip += 1
    return (str(m), i)

def run_system_tests():
    return os.environ.get("CATTIVO_TEST_SYSTEM", "0") == "1"

if run_system_tests():
    class SystemTestCase(TestCase):
        pass
else:
    class SystemTestCase(object):
        pass


init_tests()
