from __future__ import absolute_import
# Authors: John Dennis <jdennis@redhat.com>
#
# Copyright (C) 2007 Red Hat, Inc.
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.
#

# Escaping
# xmlEncodeEntitiesReentrant(), encodeEntitiesReentrant()
# xmlNewTextChild()
# stringDecodeEntities

__all__ = [
    'validate_database_doc',
    'boolean',

    'XmlSerialize',
]

import sys
from types import *
import xml.etree.ElementTree as ET

import syslog
from setroubleshoot.config import get_config
from setroubleshoot.errcode import *
from setroubleshoot.util import *


#------------------------------------------------------------------------

i18n_encoding = get_config('general', 'i18n_encoding')

#------------------------------------------------------------------------


def validate_database_doc(doc):
    if doc is None:
        log_debug("validate_database_doc: doc is empty, validate fails")
        return False
    root_node = doc.getroot()
    if root_node is None:
        log_debug("validate_database_doc: root is empty, validate fails")
        return False
    version = root_node.get('version')
    if version is None:
        log_debug("validate_database_doc: version is empty, validate fails")
        return False
    else:
        return database_version_compatible(version)


def boolean(value):
    'convert value to bool'
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        value = value.lower()
        if value in ('t', 'true', '1'):
            return True
        elif value in ('f', 'false', '0'):
            return False
        else:
            raise ValueError("cannot convert (%s) to boolean" % value)
    elif isinstance(value, int):
        return bool(value)
    else:
        raise ValueError("cannot convert (%s) to boolean" % value)

#------------------------------------------------------------------------

class XmlSerializeMetaData(type):

    def __new__(cls, classname, bases, classdict):
        #print "new: cls=%s, name=%s bases=%s dict=%s" % (cls, classname, bases, classdict)

        if classname == 'XmlSerialize':
            return type.__new__(cls, classname, bases, classdict)

        normal_init = classdict.get('__init__')
        xml_init = classdict.get('init_from_xml_node', None)
        _init_postprocess = classdict.get('_init_postprocess', None)
        if xml_init is None:
            for base_cls in bases:
                #print "searching %s" % base_cls
                xml_init = base_cls.__dict__.get('init_from_xml_node', None)
                if xml_init is not None:
                    #print "found in %s" % base_cls
                    break
        else:
            pass
            #print "found in class %s" % classname

        def wrapped_init(*args, **kwds):
            if len(args) == 2 and isinstance(args[1], ET.Element):
                xml_init(*args, **kwds)
                if _init_postprocess is not None:
                    _init_postprocess(args[0])
            else:
                normal_init(*args, **kwds)

        classdict['__init__'] = wrapped_init
        return type.__new__(cls, classname, bases, classdict)

    def __init__(cls, classname, bases, classdict):
        #print "init: cls=%s, name=%s bases=%s dict=%s" % (cls, classname, bases, classdict)
        super(XmlSerializeMetaData, cls).__init__(classname, bases, classdict)

        xml_info = classdict.get('_xml_info')
        if not xml_info:
            return
        if xml_info == 'unstructured':
            cls._unstructured = True
        else:
            cls._unstructured = False
            cls._elements = [x for x in list(xml_info.keys()) if xml_info[x]['XMLForm'] == 'element']
            cls._attributes = [x for x in list(xml_info.keys()) if xml_info[x]['XMLForm'] == 'attribute']
            cls._names = cls._elements + cls._attributes

            cls._elements.sort()
            cls._attributes.sort()
            cls._names.sort()


class XmlSerialize(object, metaclass=XmlSerializeMetaData):

    def __init__(self):
        self._init_defaults()

    def __str__(self):
        return ET.tostring(self.get_xml_nodes(), encoding="unicode")

    def _init_defaults(self):
        # Initialize each known class variable to avoid KeyError on access
        if self._xml_info == 'unstructured':
            return
        for name in self._names:
            name_info = self._xml_info[name]
            default = name_info.get('default', None)
            if default is not None:
                setattr(self, name, default())
            else:
                if name_info.get('list'):
                    setattr(self, name, [])
                else:
                    setattr(self, name, None)

    def get_elements_and_attributes(self):
        if self._unstructured:
            elements = [x for x in list(self.__dict__.keys()) if not x.startswith('_')]
            attributes = []
        else:
            elements = self._elements
            attributes = self._attributes
        return(elements, attributes)

    def get_xml_doc(self, obj_name=None):
        root = self.get_xml_nodes(obj_name)
        return ET.ElementTree(root)

    def read_xml(self, buf, obj_name=None):
        try:
            root = ET.fromstring(buf.strip())
            assert root.tag == obj_name
            self.init_from_xml_node(root)
        except ET.ParseError as e:
            syslog.syslog(syslog.LOG_ERR, "read_xml() xml.etree.ElementTree.ParseError: %s" % e)
            return

    def read_xml_file(self, xmlfile, obj_name=None, validate_doc=None):
        try:
            with open(xmlfile, 'r') as f:
                doc = ET.parse(f)
            if validate_doc:
                if not validate_doc(doc):
                    return False
            root = doc.getroot()
            assert root.tag == obj_name
            self.init_from_xml_node(root)
        except ET.ParseError as e:
            syslog.syslog(syslog.LOG_ERR, "read_xml_file() xml.etree.ElementTree.ParseError: %s" % e)
            return False
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, "read_xml_file() error: %s" % e)
            return False
        return True

    def write_xml(self, obj_name=None, f=None):
        try:
            if f is None:
                f = sys.stdout

            self.get_xml_doc(obj_name).write(f, encoding=i18n_encoding, xml_declaration=True)
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, "could not write %s: %s" % (f, e))

    def get_xml_nodes(self, obj_name=None):
        elements, attributes = self.get_elements_and_attributes()
        if obj_name is None:
            obj_name = self.__class__.__name__
        root = ET.Element(obj_name)

        for name in attributes:
            name_info = self._xml_info[name]
            typecast = name_info.get('export_typecast', str)
            value = getattr(self, name)
            if value is not None:
                root.set(name, typecast(value))

        for name in elements:
            try:
                if self._xml_info == 'unstructured':
                    typecast = str
                    list_item_name = None
                else:
                    name_info = self._xml_info[name]
                    typecast = name_info.get('export_typecast', str)
                    list_item_name = name_info.get('list')

                value = getattr(self, name)
                if value is None or isinstance(value, list) and len(value) == 0:
                    continue

                if list_item_name:
                    # Element is list container, iterate over list items
                    element_node = ET.SubElement(root, name)
                    for item in value:
                        if isinstance(item, XmlSerialize):
                            child = item.get_xml_nodes(list_item_name)
                            element_node.append(child)
                        else:
                            list_item_node = ET.SubElement(element_node, list_item_name)
                            child = typecast(item)
                            if isinstance(child, ET.Element):
                                list_item_node.append(child)
                            else:
                                list_item_node.text = child
                else:
                    # Element is scalar
                    if isinstance(value, XmlSerialize):
                        child = value.get_xml_nodes(name)
                        root.append(child)
                    else:
                        element_node = ET.SubElement(root, name)
                        child = typecast(value)
                        if isinstance(child, ET.Element):
                            element_node.append(child)
                        else:
                            element_node.text = child
            except Exception as e:
                syslog.syslog(syslog.LOG_ERR, "%s.%s value=%s" % (self.__class__.__name__, name, value))

        return root

    def init_from_xml_node(self, xml_node, obj_name=None):
        elements, attributes = self.get_elements_and_attributes()
        self._init_defaults()

        if obj_name is None:
            root = xml_node
        else:
            root = xml_node.find(obj_name)
            if root is None:
                raise KeyError("xml child element (%s) not found in node %s" % (obj_name, xml_node.tag))

        # Read the attributes in the xml node Cast the attribute value
        # to a Python type and store coerced value in the Python
        # object (self) which can then be accessed by "name"

        for name, value in root.items():
            if name not in attributes:
                log_debug("unknown attribute (%s) found in xml element (%s)" % (name, root.tag))
                continue
            name_info = self._xml_info[name]
            typecast = name_info.get('import_typecast', str)
            if isinstance(typecast, type) and issubclass(typecast, XmlSerialize):
                raise ValueError("Illegal use of substructure in attribute (%s)" % name)
            else:
                self.__setattr__(name, typecast(value))

        for element_node in root:
            name = element_node.tag
            if self._unstructured:
                # Unstructured data, store the string content of each
                # element in the Python object (self) which can then
                # be accessed by "name"
                value = "".join(element_node.itertext())
                self.__setattr__(name, value)
            else:
                # Recursively read the contents of each element.  Casting to a
                # Python types along the recursion path and store the final
                # Python value in the Python object (self) which can then be
                # accessed by "name"
                if name not in elements:
                    log_debug("unknown element (%s) found in xml element (%s)" % (name, root.tag))
                    continue
                name_info = self._xml_info[name]
                typecast = name_info.get('import_typecast', str)
                # Does this node have substructure?
                list_item_name = name_info.get('list')
                if list_item_name:
                    # Element is a list, recursively iterate over the elements children, e.g. list elements
                    attr = getattr(self, name, [])
                    list_nodes = element_node.findall(list_item_name)
                    if isinstance(typecast, type) and issubclass(typecast, XmlSerialize):
                        for list_node in list_nodes:
                            attr.append(typecast(list_node))
                    else:
                        for list_node in list_nodes:
                            attr.append(typecast("".join(list_node.itertext())))
                else:
                    if isinstance(typecast, type) and issubclass(typecast, XmlSerialize):
                        self.__setattr__(name, typecast(element_node))
                    else:
                        value = "".join(element_node.itertext())
                        self.__setattr__(name, typecast(value))
