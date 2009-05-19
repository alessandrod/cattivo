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

from urllib import unquote

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY

try:
    from urlparse import parse_qs
except ImportError:
    def parse_qs(qs, keep_blank_values=0, strict_parsing=0, unquote=unquote):
        """like cgi.parse_qs, only with custom unquote function"""
        d = {}
        items = [s2 for s1 in qs.split("&") for s2 in s1.split(";")]
        for item in items:
            try:
                k, v = item.split("=", 1)
            except ValueError:
                if strict_parsing:
                    raise
                continue
            if v or keep_blank_values:
                k = unquote(k.replace("+", " "))
                v = unquote(v.replace("+", " "))
                if k in d:
                    d[k].append(v)
                else:
                    d[k] = [v]
        return d
