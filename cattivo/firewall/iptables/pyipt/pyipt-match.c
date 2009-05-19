
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

#include <getopt.h>

#include "pyipt-match.h"

static PyObject *
py_ipt_match_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"name", "arguments", NULL};
  PyIPTMatchObject *self = NULL;
  char *name;
  PyObject *arguments = NULL;
  int argc = 0;
  char **argv = NULL;
  struct xtables_match *match;
  int invert = 0;
  int i;
  int size;
  char c;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "z|O", kwlist,
      &name, &arguments))
    goto error;

  if (arguments && !PySequence_Check (arguments))
    goto error;

  self = (PyIPTMatchObject *) type->tp_alloc (type, 0);
  if (self == NULL)
    goto error;

  self->match = NULL;
  match = xtables_find_match (name, XTF_TRY_LOAD, &self->match);
  if (match == NULL) {
    PyErr_SetString (PyIPTException, "can't find match");
    goto error;
  }
  
  /* almost verbatim copy of iptables.c stuff. So much for code reuse */
  size = IPT_ALIGN(sizeof(struct ipt_entry_match))
       + match->size;
  match->m = calloc(1, size);
  match->m->u.match_size = size;
  strcpy(match->m->u.user.name, match->name);
  xtables_set_revision(match->m->u.user.name, match->revision);
  if (match->init != NULL)
    match->init(match->m);

  if (arguments) {
    /* convert arguments to argv */
    argc = PySequence_Size (arguments);
    argv = malloc (sizeof (char *) * (argc + 1));
    argv[0] = "pyipt";
    for (i = 0; i < argc; ++i) {
      PyObject *arg = PySequence_GetItem (arguments, i);
      if (!PyString_Check (arg)) {
        PyErr_SetString (PyExc_TypeError, "arguments must be a list of strings");
        goto error;
      }

      argv[i+1] = PyString_AS_STRING (arg);
    }

    /* parse match specific opts */
    /* FIXME: we don't pass entry (NULL) here */
    optind = 1;
    while ((c = getopt_long (argc+1, argv, "", match->extra_opts, NULL)) != -1) {
      switch (c) {
        case -1:
          break;

        case ':':
          PyErr_SetString (PyIPTException, "missing argument");
          goto error;
          break;

        default:
          if (!match->parse(c, argv, invert,
              &match->mflags, NULL, &match->m) || py_ipt_xt_get_error ()) {
            if (py_ipt_xt_get_error ()) {
              PyErr_SetString (PyIPTException, py_ipt_xt_get_error_message ());
            } else {
              PyErr_SetString (PyIPTException, "invalid match arguments");
            }

            goto error;
          }
      }
    }

    free (argv);
  }

  return (PyObject *) self;

error:
  if (argv)
    free (argv);

  Py_XDECREF (self);
  return NULL;
}

static void
py_ipt_match_dealloc (PyObject *obj)
{
  PyIPTMatchObject *self = (PyIPTMatchObject *) obj;

  if (self->match)
    free (self->match);

  self->ob_type->tp_free (obj);
}

static int
py_ipt_match_init (PyObject *obj, PyObject *args, PyObject *kwds)
{
  return 0;
}

static PyMethodDef py_ipt_match_methods[] = {
    {NULL}  /* Sentinel */
};

PyTypeObject PyIPTMatchType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "pyipt.Match",             /*tp_name*/
    sizeof(PyIPTMatchObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    py_ipt_match_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "Match object",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    py_ipt_match_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)py_ipt_match_init,      /* tp_init */
    0,                         /* tp_alloc */
    py_ipt_match_new,                 /* tp_new */
};
