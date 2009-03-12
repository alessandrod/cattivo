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

#include "pyipt.h"
#include "pyipt-match.h"
#include "pyipt-target.h"

typedef struct {
    PyObject_HEAD
    struct ipt_entry entry;
    struct in_addr *source;
    struct in_addr *destination;
    char *jump;
    char *in_interface;
    char *out_interface;
    PyObject *matches;
    PyIPTTargetObject *target;
} PyIPTEntryObject;

extern PyTypeObject PyIPTMatchType;
extern PyTypeObject PyIPTTargetType;
extern PyTypeObject PyIPTEntryType;
extern PyTypeObject PyIPTTableType;

static PyObject *
py_ipt_entry_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"source", "destination", "jump",
      "in_interface", "out_interface", NULL};
  PyIPTEntryObject *self = NULL;
  char *source = NULL;
  char *destination = NULL;
  char *jump = NULL;
  char *in_interface = NULL;
  char *out_interface = NULL;
  unsigned int  n_source_addresses = 0;
  unsigned int  n_destination_addresses = 0;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "|zzzzz", kwlist, &source,
    &destination, &jump, &in_interface, &out_interface))
    goto error;

  self = (PyIPTEntryObject *) type->tp_alloc (type, 0);
  if (self == NULL)
    goto error;

  self->source = NULL;
  self->destination = NULL;
  self->jump = NULL;
  self->in_interface = NULL;
  self->out_interface = NULL;
  self->matches = NULL;
  self->target = NULL;

  if (source == NULL)
    source = "0.0.0.0/0";

  xtables_ipparse_any (source, &self->source, &self->entry.ip.smsk, &n_source_addresses);
  if (n_source_addresses != 1) {
    PyErr_SetString (PyIPTException,
        "multiple source addresses are not allowed.");
    goto error;
  }

  if (destination == NULL)
    destination = "0.0.0.0/0";

  xtables_ipparse_any (destination, &self->destination, &self->entry.ip.dmsk, &n_destination_addresses);
  if (n_destination_addresses != 1) {
    PyErr_SetString (PyIPTException,
        "multiple destination addresses are not allowed.");
    goto error;
  }
  
  if (in_interface) { 
    xtables_parse_interface(in_interface, self->entry.ip.iniface, self->entry.ip.iniface_mask);
    if (py_ipt_xt_get_error ()) {
      PyErr_SetString (PyIPTException, py_ipt_xt_get_error_message ());
      goto error;
    }
  }
 
  if (out_interface) { 
    xtables_parse_interface(out_interface, self->entry.ip.outiface, self->entry.ip.outiface_mask);
    if (py_ipt_xt_get_error ()) {
      PyErr_SetString (PyIPTException, py_ipt_xt_get_error_message ());
      goto error;
    }
  }

  if (jump)
    self->jump = strdup (jump);
  else
    self->jump = NULL;

  if (in_interface)
    self->in_interface = strdup (in_interface);
  else
    self->in_interface = NULL;

  if (out_interface)
    self->out_interface = strdup (out_interface);
  else
    self->out_interface = NULL;

  self->matches = PyList_New (0);

  return (PyObject *) self;

error:
  Py_XDECREF (self);
  return NULL;
}

static void
py_ipt_entry_dealloc (PyObject *obj)
{
  PyIPTEntryObject *self = (PyIPTEntryObject *) obj;

  if (self->source)
    free (self->source);

  if (self->destination)
    free (self->destination);

  if (self->jump)
    free (self->jump);

  if (self->in_interface)
    free (self->in_interface);

  if (self->out_interface)
    free (self->out_interface);

  Py_XDECREF (self->matches);
  Py_XDECREF (self->target);

  self->ob_type->tp_free (obj);
}

static int
py_ipt_entry_init (PyObject *obj, PyObject *args, PyObject *kwds)
{
  return 0;
}

static PyObject *
py_ipt_entry_add_match (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"match", NULL};
  PyIPTEntryObject *self = (PyIPTEntryObject *) obj;
  PyObject *match = NULL;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O!", kwlist,
        &PyIPTMatchType, &match))
    return NULL;

  if (PySequence_Contains (self->matches, match)) {
    PyErr_SetString (PyIPTException, "match already added");
    return NULL;
  }

  PyList_Append (self->matches, match);
  
  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_entry_remove_match (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"match", NULL};
  PyIPTEntryObject *self = (PyIPTEntryObject *) obj;
  PyObject *match = NULL;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O!", kwlist,
        &PyIPTMatchType, &match))
    return NULL;

  if (PyObject_CallMethod (self->matches, "remove", "(O)", match) == NULL) {
    PyErr_Clear();
    PyErr_SetString (PyIPTException, "match not in entry");
    return NULL;
  }
  
  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_entry_set_target (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"target", NULL};
  PyIPTEntryObject *self = (PyIPTEntryObject *) obj;
  PyIPTTargetObject *target = NULL;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O!", kwlist,
        &PyIPTTargetType, &target))
    return NULL;

  Py_XDECREF (self->target);

  Py_INCREF (target);
  self->target = target;
  
  Py_INCREF (Py_None);
  return Py_None;
}

struct ipt_entry *
py_ipt_entry_generate (PyObject *obj)
{
  PyIPTEntryObject *self;
  struct ipt_entry *entry;
  PyIPTMatchObject *match;
	unsigned int size;
  int i;

  self = (PyIPTEntryObject *) obj;

	size = sizeof(struct ipt_entry);

  for (i = 0; i < PySequence_Length (self->matches); ++i) {
    match = (PyIPTMatchObject *) PySequence_GetItem (self->matches, i);
    size += match->match->match->m->u.match_size;
  }

	entry = xtables_malloc(size + self->target->target->t->u.target_size);
	*entry = self->entry;
  entry->ip.invflags = 0;
  entry->ip.src = *self->source;
  entry->ip.dst = *self->destination;
  /* FIXME: make this an argument to __init__ */
  entry->ip.proto = IPPROTO_TCP;
  entry->target_offset = size;
	entry->next_offset = size + self->target->target->t->u.target_size;
  
  size = 0;
  for (i = 0; i < PySequence_Length (self->matches); ++i) {
    match = (PyIPTMatchObject *) PySequence_GetItem (self->matches, i);
    memcpy (entry->elems + size, match->match->match->m,
        match->match->match->m->u.match_size);
    size += match->match->match->m->u.match_size;
  }

	memcpy(entry->elems + size, self->target->target->t,
      self->target->target->t->u.target_size);

	return entry;
}

static PyMethodDef py_ipt_entry_methods[] = {
    {"addMatch", (PyCFunction) py_ipt_entry_add_match,
        METH_VARARGS | METH_KEYWORDS, "add a new match"},
    {"removeMatch", (PyCFunction) py_ipt_entry_remove_match,
        METH_VARARGS | METH_KEYWORDS, "remove a match"},
    {"setTarget", (PyCFunction) py_ipt_entry_set_target,
        METH_VARARGS | METH_KEYWORDS, "set target"},
    {NULL}  /* Sentinel */
};

PyTypeObject PyIPTEntryType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "pyipt.Entry",             /*tp_name*/
    sizeof(PyIPTEntryObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    py_ipt_entry_dealloc,                         /*tp_dealloc*/
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
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "Entry object",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    py_ipt_entry_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)py_ipt_entry_init,      /* tp_init */
    0,                         /* tp_alloc */
    py_ipt_entry_new,                 /* tp_new */
};

