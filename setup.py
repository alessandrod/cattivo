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

from distutils.core import setup, Extension

# xtables
xtables_dir = "cattivo/firewall/iptables/xtables/"
xtables_extensions_dir = "cattivo/firewall/iptables/xtables/extensions/"
xtables_sources = [xtables_dir + source
        for source in ["xtables.c", "extensions/libxt_tcp.c",
                "extensions/libxt_state.c", "extensions/libxt_standard.c",
                "extensions/libxt_TPROXY.c", "extensions/libxt_MARK.c",
                "extensions/libxt_socket.c", "extensions/libxt_NFLOG.c"]]
xtables_define_macros = [("XTABLES_LIBDIR", "\"%s\"" % 
        (xtables_dir + "extensions/"))]

# libiptc
libiptc_dir = "cattivo/firewall/iptables/libiptc/"
libiptc_sources = [libiptc_dir + source
        for source in ["libip4tc.c"]]

# pyipt
pyipt = "cattivo.firewall.iptables.pyipt"
pyipt_dir = "cattivo/firewall/iptables/pyipt/"
pyipt_sources = [pyipt_dir + source 
        for source in ["pyipt.c", "pyipt-match.c", "pyipt-target.c",
                "pyipt-entry.c", "pyipt-table.c"]]

iptables_dir = "cattivo/firewall/iptables/"

setup(name="cattivo",
    version="0.1",
    license="GPL",
    description="cattivo is a minimalistic captive portal",
    author="Alessandro Decina",
    author_email="alessandro.d@gmail.com",
    url="http://people.freedesktop.org/~alessandro/cattivo/",
    packages=["cattivo"],
    ext_modules=[Extension(name=pyipt,
            sources=libiptc_sources + xtables_sources + pyipt_sources,
            include_dirs=[iptables_dir, libiptc_dir, xtables_dir,
                    xtables_extensions_dir, pyipt_dir],
            libraries=['dl'],
            define_macros=xtables_define_macros)],
            extra_link_args=["-E"]
)
