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

from tests.common import new_client_id
from unittest import TestCase

from cattivo.logger.http.client import Logger
from cattivo.utils import parse_qs

try:
    import simplejson as json
except ImportError:
    import json

class FakeLogger(Logger):
    def doRequest(self, url, data):
        self.__dict__.setdefault("requests", []).append((url, data))

class TestLogger(TestCase):
    def testLog(self):
        logger = FakeLogger()
        client_id = new_client_id()

        logger.logHTTP(client_id, "1.2.3.4", 80,
                "www.example.net", "/index.html")
        
        self.failUnlessEqual(len(logger.requests), 1)
        
        url, encoded_data = logger.requests[0]
        data_dict = parse_qs(encoded_data)
        data = json.loads(data_dict["data"][0])
        del data["timestamp"]
        self.failUnlessEqual(url, "http://localhost/log/client/0")
        self.failUnlessEqual(data, {"client_id": client_id[0],
                "destination": "1.2.3.4", "port": 80,
                "http_host": "www.example.net",
                "http_resource": "/index.html"})

