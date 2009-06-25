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

import ctypes
import ctypes.util
import sys
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

def _get_libc_name():
    if sys.platform == 'win32':
        # Parses sys.version and deduces the version of the compiler
        import distutils.msvccompiler
        version = distutils.msvccompiler.get_build_version()
        if version is None:
            # This logic works with official builds of Python.
            if sys.version_info < (2, 4):
                clibname = 'msvcrt'
            else:
                clibname = 'msvcr71'
        else:
            if version <= 6:
                clibname = 'msvcrt'
            else:
                clibname = 'msvcr%d' % (version * 10)

        # If python was built with in debug mode
        import imp
        if imp.get_suffixes()[0][0] == '_d.pyd':
            clibname += 'd'

        return clibname+'.dll'
    else:
        return ctypes.util.find_library('c')

def _somehow_get_errno(standard_c_lib):
    # Python 2.5 or older
    if sys.platform == 'win32':
        standard_c_lib._errno.restype = ctypes.POINTER(ctypes.c_int)
        def _where_is_errno():
            return standard_c_lib._errno()

    elif sys.platform in ('linux2', 'freebsd6'):
        standard_c_lib.__errno_location.restype = ctypes.POINTER(ctypes.c_int)
        def _where_is_errno():
            return standard_c_lib.__errno_location()

    elif sys.platform in ('darwin', 'freebsd7'):
        standard_c_lib.__error.restype = ctypes.POINTER(ctypes.c_int)
        def _where_is_errno():
            return standard_c_lib.__error()

    return lambda: _where_is_errno().contents.value

if hasattr(ctypes, "get_errno"):
    get_errno = ctypes.get_errno
else:
    _libc_name = _get_libc_name()
    _standard_c_lib = ctypes.cdll.LoadLibrary(_libc_name)
    get_errno = _somehow_get_errno(_standard_c_lib)
