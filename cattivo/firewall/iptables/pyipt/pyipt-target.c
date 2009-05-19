
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

#include "pyipt-target.h"
#include "pyipt-table.h"

static PyObject *
py_ipt_target_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"name", "arguments", "table", NULL};
  PyIPTTargetObject *self = NULL;
  char *name, *chain = NULL;
  PyObject *arguments = NULL;
  PyObject *table = NULL;
  int argc = 0;
  const char **argv = NULL;
  struct xtables_target *target, *target_orig;
  int invert = 0;
  int i;
  int size;
  char c;
  struct iptc_handle *handle;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "z|OO!", kwlist,
      &name, &arguments, &PyIPTTableType, &table))
    goto error;

  if (arguments && !PySequence_Check (arguments))
    goto error;

  self = (PyIPTTargetObject *) type->tp_alloc (type, 0);
  if (self == NULL)
    goto error;

  self->target = NULL;

  if (table) {
    handle = py_ipt_table_get_handle (table);
    if (iptc_is_chain (name, handle)) {
      chain = name;
      name = "standard";
    }
  }

  target_orig = xtables_find_target (name, XTF_TRY_LOAD);
  if (target_orig == NULL) {
    PyErr_SetString (PyIPTException, "can't find target");
    goto error;
  }

  target = (struct xtables_target *) malloc (sizeof (struct xtables_target));
  memcpy (target, target_orig, sizeof (struct xtables_target));

  /* almost verbatim copy of iptables.c stuff. So much for code reuse */
  size = IPT_ALIGN(sizeof(struct ipt_entry_target))
    + target->size;

  target->t = xtables_calloc(1, size);
  target->t->u.target_size = size;
  
  if (chain) { 
    strcpy(target->t->u.user.name, chain);
  } else {
    strcpy(target->t->u.user.name, name);
    xtables_set_revision(target->t->u.user.name, target->revision);
  }
  
  if (target->init != NULL)
    target->init(target->t); 

  if (arguments && PySequence_Size (arguments)) { 
    /* convert arguments to argv */
    argc = PySequence_Size (arguments);
    argv = (const char *) malloc (sizeof (char *) * (argc + 1));
    argv[0] = "pyipt";
    for (i = 0; i < argc; ++i) {
      PyObject *arg = PySequence_GetItem (arguments, i);
      if (!PyString_Check (arg)) {
        PyErr_SetString (PyExc_TypeError, "arguments must be a list of strings");
        goto error;
      }

      argv[i+1] = PyString_AS_STRING (arg);
    }

    /* parse target specific opts */
    /* FIXME: we don't pass entry (NULL) here */
    optind = 1;
    while ((c = getopt_long (argc+1, argv, "", target->extra_opts, NULL)) != -1) {
      switch (c) {
        case -1:
          break;

        case ':':
          PyErr_SetString (PyIPTException, "missing argument");
          goto error;
          break;

        default:
          if (!target->parse(c, argv, invert,
              &target->tflags, NULL, &target->t) || py_ipt_xt_get_error ()) {
            if (py_ipt_xt_get_error ()) {
              PyErr_SetString (PyIPTException, py_ipt_xt_get_error_message ());
            } else {
              PyErr_SetString (PyIPTException, "invalid target arguments");
            }

            goto error;
          }
      }
    }

    free (argv);
  }

  self->target = target;

  return (PyObject *) self;

error:
  if (argv)
    free (argv);

  Py_XDECREF (self);
  return NULL;
}

static void
py_ipt_target_dealloc (PyObject *obj)
{
  PyIPTTargetObject *self = (PyIPTTargetObject *) obj;

  if (self->target) {
    free (self->target->t);
    free (self->target);
  }

  self->ob_type->tp_free (obj);
}

static int
py_ipt_target_init (PyObject *obj, PyObject *args, PyObject *kwds)
{
  return 0;
}

static PyMethodDef py_ipt_target_methods[] = {
    {NULL}  /* Sentinel */
};

PyTypeObject PyIPTTargetType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "pyipt.Target",             /*tp_name*/
    sizeof(PyIPTTargetObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    py_ipt_target_dealloc,                         /*tp_dealloc*/
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
    "Target object",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    py_ipt_target_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)py_ipt_target_init,      /* tp_init */
    0,                         /* tp_alloc */
    py_ipt_target_new,                 /* tp_new */
};

