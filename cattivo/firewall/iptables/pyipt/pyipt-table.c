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
#include "pyipt-entry.h"

typedef struct {
    PyObject_HEAD
    char *table;
    struct iptc_handle *handle;
} PyIPTTableObject;

static PyObject *
py_ipt_table_new (PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"table", NULL};
  char *table_name;
  PyIPTTableObject *self = NULL;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "s", kwlist, &table_name))
    goto error;

  self = (PyIPTTableObject *) type->tp_alloc (type, 0);
  if (self == NULL)
    goto error;

  self->handle = NULL;
  self->table = NULL;

  self->handle = iptc_init (table_name);
  if (self->handle == NULL) {
    PyErr_SetFromErrno (PyIPTException);
    goto error;
  }

  self->table = strdup (table_name);
  
  return (PyObject *) self;

error:
  Py_XDECREF (self);
  return NULL;
}

static void
py_ipt_table_dealloc (PyObject *oself)
{
  PyIPTTableObject *self = (PyIPTTableObject *) oself;

  if (self->table)
    free (self->table);

  if (self->handle != NULL)
    iptc_free (&self->handle);

  self->ob_type->tp_free (oself);
}

static int
py_ipt_table_init (PyObject *oself, PyObject *args, PyObject *kwds)
{
  return 0;
}

static PyObject *
py_ipt_table_create_chain (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"name", NULL};
  char *chain_name;
  PyIPTTableObject *self = (PyIPTTableObject *) obj;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "s", kwlist, &chain_name))
    return NULL;

  if (!iptc_create_chain (chain_name, &self->handle)) {
    PyErr_SetFromErrno (PyIPTException);
    return NULL;
  }

  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_table_delete_chain (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"chain", NULL};
  char *chain_name;
  PyIPTTableObject *self = (PyIPTTableObject *) obj;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "s", kwlist, &chain_name))
    return NULL;

  if (!iptc_delete_chain (chain_name, &self->handle)) {
    PyErr_SetFromErrno (PyIPTException);
    return NULL;
  }
  
  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_table_flush_entries (PyTypeObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"chain", NULL};
  char *chain_name;
  PyIPTTableObject *self = (PyIPTTableObject *) obj;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "s", kwlist, &chain_name))
    return NULL;

  if (!iptc_flush_entries (chain_name, &self->handle)) {
    PyErr_SetFromErrno (PyIPTException);
    return NULL;
  }
  
  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_table_append_entry (PyTypeObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"entry", "chain", NULL};
  PyIPTTableObject *self = (PyIPTTableObject *) obj;
  PyObject *entry;
  char *chain;
  struct ipt_entry *ip_entry;
  int ret;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O!s", kwlist,
        &PyIPTEntryType, &entry, &chain))
    return NULL;

  ip_entry = py_ipt_entry_generate (entry);
  ret = iptc_append_entry(chain, ip_entry, &self->handle);
  free (ip_entry);

	return PyBool_FromLong(ret);
}

static PyObject *
py_ipt_table_delete_entry (PyTypeObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"entry", "chain", NULL};
  PyIPTTableObject *self = (PyIPTTableObject *) obj;
  PyObject *entry;
  char *chain;
  struct ipt_entry *ip_entry;
  int ret = 0;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "O!s", kwlist,
        &PyIPTEntryType, &entry, &chain))
    return NULL;

  ip_entry = py_ipt_entry_generate (entry);
  //ret = iptc_append_entry(chain, ip_entry, &self->handle);
  free (ip_entry);

  if (!ret) {
    PyErr_SetFromErrno (PyIPTException);
    return NULL;
  } 

  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
py_ipt_table_commit (PyObject *obj, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {NULL};
  PyIPTTableObject *self = (PyIPTTableObject *) obj;

  if (!PyArg_ParseTupleAndKeywords (args, kwds, "", kwlist))
    return NULL;

  ret = iptc_commit (&self->handle);
  if (!ret) {
    PyErr_SetFromErrno (PyIPTException);
    return NULL;
  } 

  Py_INCREF (Py_None);
  return Py_None;
}

static PyMethodDef py_ipt_table_methods[] = {
    {"createChain", (PyCFunction) py_ipt_table_create_chain,
        METH_VARARGS | METH_KEYWORDS, "create a new chain"},
    {"deleteChain", (PyCFunction) py_ipt_table_delete_chain,
        METH_VARARGS | METH_KEYWORDS, "delete a chain"},
    {"flushEntries", (PyCFunction) py_ipt_table_flush_entries,
        METH_VARARGS | METH_KEYWORDS,
        "flush all the entries contained in a chain"},
    {"appendEntry", (PyCFunction) py_ipt_table_append_entry,
        METH_VARARGS | METH_KEYWORDS, "insert a new entry in a chain"},
    {"deleteEntry", (PyCFunction) py_ipt_table_delete_entry,
        METH_VARARGS | METH_KEYWORDS, "delete an entry from a chain"},
    {"commit", (PyCFunction) py_ipt_table_commit,
        METH_VARARGS | METH_KEYWORDS, "commit changes to the ruleset"},
    {NULL}  /* Sentinel */
};

PyTypeObject PyIPTTableType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "pyipt.Table",             /*tp_name*/
    sizeof(PyIPTTableObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    py_ipt_table_dealloc,                         /*tp_dealloc*/
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
    "Table object",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    py_ipt_table_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)py_ipt_table_init,      /* tp_init */
    0,                         /* tp_alloc */
    py_ipt_table_new,                 /* tp_new */
};
