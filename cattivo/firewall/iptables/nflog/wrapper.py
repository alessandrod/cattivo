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
from cattivo.utils import get_errno
from array import array

from twisted.internet import fdesc
from socket import AF_INET

NFULNL_COPY_PACKET = 0x02

try:
    nflogDll = CDLL("libnetfilter_log.so.1", use_errno=True)
except TypeError:
    nflogDll = CDLL("libnetfilter_log.so.1")

nflogFunctions = ["nflog_open", "nflog_close", "nflog_nfnlh",
        "nflog_fd", "nfnl_catch", "nflog_bind_group",
        "nflog_callback_register", "nflog_set_mode",
        "nflog_bind_pf", "nflog_get_uid", "nflog_get_gid",
        "nflog_get_payload"]
for functionName in nflogFunctions:
    try:
        globals()[functionName] = getattr(nflogDll, functionName)
    except AttributeError:
        continue


# nflog callback
# static int callback(struct nflog_g_handle *gh, struct nfgenmsg *nfmsg,
# 		  struct nflog_data *nfa, void *data)
# -1 == Failure
NFLogCallback = CFUNCTYPE(c_int, c_voidp, c_voidp, c_voidp, py_object)

def nflog_callback_impl(nflog_g_handle, nfmsg, nfdata, user_data):
    data = NFLogData(c_voidp(nfdata))
    return user_data.callback(nfmsg, data)

nflog_callback = NFLogCallback(nflog_callback_impl)

c_uint8p = POINTER(c_uint8)

def call_nf(call, *args, **kw):
    error = kw.pop("error", -1)
    ret = call(*args, **kw)
    if ret == error:
        error = get_errno()
        string = os.strerror(error)
        raise OSError(error, string)

    return ret

class NFLogError(Exception):
    pass


class NFLogData(object):
    def __init__(self, data):
        self.data = data

    def getUid(self):
        uid = c_uint32()
        call_nf(nflog_get_uid, self.data, byref(uid))

        return uid

    def getGid(self):
        gid = c_uint32()
        call_nf(nflog_get_gid, self.data, byref(gid))

        return gid

    def getPayload(self):
        buffer_p = c_uint8p()
        buffer_len = call_nf(nflog_get_payload, self.data, byref(buffer_p))
        buf = array("B", buffer_p[:buffer_len])

        return buf

class NFLog(object):
    nflog_handle = 0
    nflog_g_handle = 0
    nfnl_handle = 0
    fd = None
    callback = None
    non_blocking = True

    def open(self):
        self.nflog_handle = call_nf(nflog_open, error=0)
        self.nfnl_handle = call_nf(nflog_nfnlh, self.nflog_handle, error=0)
        self.fd = nflog_fd(self.nflog_handle)
        if self.non_blocking:
            # set the fd non blocking so we can use nfnl_catch to do the processing
            fdesc.setNonBlocking(self.fd)

    def close(self):
        if self.nflog_handle == 0:
            raise NFLogError()

        call_nf(nflog_close, self.nflog_handle)
        self.nflog_handle = 0
        self.nflog_g_handle = 0
        self.nfnl_handle = 0
        self.fd = -1

    def bindProtocolFamily(self, family):
        if self.nflog_handle == 0:
            raise NFLogError()

        call_nf(nflog_bind_pf, self.nflog_handle, family)

    def bindGroup(self, group):
        if self.nflog_handle == 0:
            raise NFLogError()

        self.nflog_g_handle = \
                c_voidp(call_nf(nflog_bind_group,
                        self.nflog_handle, group, error=0))
    
    def setMode(self, mode, range_):
        call_nf(nflog_set_mode, self.nflog_g_handle, mode, range_)

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

        call_nf(nfnl_catch, self.nfnl_handle)

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
