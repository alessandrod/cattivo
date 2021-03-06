/* Copyright (C) 2009 Alessandro Decina
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#ifndef PY_IPT_H
#define PY_IPT_H

#include <Python.h>
#include <libiptc/libiptc.h>
#include <xtables.h>

#ifndef INSIDE_PY_IPT_C
extern PyObject *PyIPTException;
#else
PyObject *PyIPTException;
#endif

enum xtables_exittype py_ipt_xt_get_error ();
const char *py_ipt_xt_get_error_message ();

#endif /* PY_IPT_H */
