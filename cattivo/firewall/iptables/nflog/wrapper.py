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
from ctypes import *

from twisted.internet import fdesc
from socket import AF_INET

NFULNL_COPY_PACKET = 0x02

nflogDll = CDLL("libnetfilter_log.so.1", use_errno=True)
nflogFunctions = ["nflog_open", "nflog_close", "nflog_nfnlh",
        "nflog_fd", "nfnl_catch", "nflog_bind_group",
        "nflog_callback_register", "nflog_set_mode",
        "nflog_bind_pf"]
for functionName in nflogFunctions:
    globals()[functionName] = getattr(nflogDll, functionName)


# nflog callback
# static int callback(struct nflog_g_handle *gh, struct nfgenmsg *nfmsg,
# 		  struct nflog_data *nfa, void *data)
# -1 == Failure
NFLogCallback = CFUNCTYPE(c_int, c_voidp, c_voidp, c_voidp, py_object)

def nflog_callback_impl(nflog_g_handle, nfmsg, nfdata, user_data):
    return user_data.callback(nfmsg, nfdata)

nflog_callback = NFLogCallback(nflog_callback_impl)


class NFLogError(Exception):
    pass


class NFLog(object):
    nflog_handle = 0
    nflog_g_handle = 0
    nfnl_handle = 0
    fd = None
    callback = None
    non_blocking = True

    def open(self):
        self.nflog_handle = c_voidp(nflog_open())
        if self.nflog_handle == 0:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

        self.nfnl_handle = c_voidp(nflog_nfnlh(self.nflog_handle))
        if self.nfnl_handle == 0:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

        self.fd = nflog_fd(self.nflog_handle)
        if self.non_blocking:
            # set the fd non blocking so we can use nfnl_catch to do the processing
            fdesc.setNonBlocking(self.fd)

    def close(self):
        if self.nflog_handle == 0:
            raise NFLogError()

        ret = nflog_close(self.nflog_handle)
        if ret == -1:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

        self.nflog_handle = 0
        self.nflog_g_handle = 0
        self.nfnl_handle = 0
        self.fd = -1

    def bindProtocolFamily(self, family):
        if self.nflog_handle == 0:
            raise NFLogError()

        ret = nflog_bind_pf(self.nflog_handle, family)
        if ret == -1:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

    def bindGroup(self, group):
        if self.nflog_handle == 0:
            raise NFLogError()

        self.nflog_g_handle = \
                c_voidp(nflog_bind_group(self.nflog_handle, group))
        if self.nflog_g_handle == 0:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)
    
    def setMode(self, mode, range_):
        ret = nflog_set_mode(self.nflog_g_handle, mode, range_)
        if ret == -1:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

    def setCallback(self, callback):
        assert self.callback is None
        if self.nflog_g_handle == 0:
            raise NFLogError()

        self.callback = callback
        obj = py_object(self)
        nflog_callback_register(self.nflog_g_handle, nflog_callback, obj)

    def catch(self):
        if self.nfnl_handle == 0:
            raise NFLogError()

        ret = nfnl_catch(self.nfnl_handle)
        if ret == -1:
            error = get_errno()
            string = os.strerror(error)
            raise OSError(error, string)

if __name__ == "__main__":
    def nflogCallback(*args):
        import pdb; pdb.set_trace()
    wrapper = NFLog()
    wrapper.non_blocking = False
    wrapper.open()
    wrapper.bindProtocolFamily(AF_INET)
    wrapper.bindGroup(0)
    wrapper.setMode(NFULNL_COPY_PACKET, 0xFFFF)
    wrapper.setCallback(nflogCallback)
    wrapper.catch()
