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

#define INSIDE_PY_IPT_C
#include "pyipt.h"
#include "pyipt-match.h"
#include "pyipt-target.h"
#include "pyipt-entry.h"
#include "pyipt-table.h"

extern void libxt_tproxy_init();
extern void libxt_standard_init();
extern void libxt_tcp_init ();
extern void libxt_state_init ();
extern void libxt_mark_init ();
extern void libxt_socket_init ();
extern void libxt_nflog_init ();

extern PyTypeObject PyIPTMatchType;
extern PyTypeObject PyIPTTargetType;
extern PyTypeObject PyIPTEntryType;
extern PyTypeObject PyIPTTableType;

static enum xtables_exittype py_ipt_xt_error;
static char py_ipt_xt_error_message[1024];

void exit_error (enum xtables_exittype status, const char *msg, ...)
{
  va_list args;

  py_ipt_xt_error = status;

  va_start (args, msg);
  vsnprintf (py_ipt_xt_error_message, 1024, msg, args);
  va_end (args);
}

static struct xtables_globals py_ipt_xt_globals = {
  .option_offset = 0,
  .program_name = "pyipt",
  .program_version = "0.1",
  .orig_opts = NULL,
  .opts = NULL,
  .exit_err = exit_error
};

enum xtables_exittype py_ipt_xt_get_error ()
{
  return py_ipt_xt_error;
}

const char *py_ipt_xt_get_error_message ()
{
  return py_ipt_xt_error_message;
}

static PyMethodDef py_ipt_methods[] = {
    {NULL}  /* Sentinel */
};

PyMODINIT_FUNC
initpyipt()
{
  PyObject *module = NULL;

  xtables_init ();
  xtables_set_params (&py_ipt_xt_globals);
  xtables_set_nfproto(NFPROTO_IPV4);

  libxt_standard_init();
  libxt_tcp_init();
  libxt_state_init();
  libxt_tproxy_init();
  libxt_mark_init();
  libxt_socket_init();
  libxt_nflog_init();

  module = Py_InitModule ("pyipt", py_ipt_methods);
  if (module == NULL)
    return;

  PyIPTException = PyErr_NewException ("pyipt.IPTablesError",
      PyExc_BaseException, NULL);
  if (PyIPTException == NULL)
    goto error;

  PyModule_AddObject (module, "IPTablesError", PyIPTException);

  if (PyType_Ready(&PyIPTMatchType) < 0)
      goto error;

  Py_INCREF (&PyIPTMatchType);
  PyModule_AddObject (module, "Match", (PyObject *)&PyIPTMatchType);
  
  if (PyType_Ready(&PyIPTTargetType) < 0)
      goto error;

  Py_INCREF (&PyIPTTargetType);
  PyModule_AddObject (module, "Target", (PyObject *)&PyIPTTargetType);
  
  if (PyType_Ready(&PyIPTEntryType) < 0)
      goto error;

  Py_INCREF (&PyIPTEntryType);
  PyModule_AddObject (module, "Entry", (PyObject *)&PyIPTEntryType);
  
  if (PyType_Ready(&PyIPTTableType) < 0)
      goto error;

  Py_INCREF (&PyIPTTableType);
  PyModule_AddObject (module, "Table", (PyObject *)&PyIPTTableType);

  return;

error:
  Py_DECREF (module);
}
