#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 3/28/12
@author: eis
"""
import os
from fw.qt import *

_def_param_type = 'QVariant'
variant = _def_param_type

class Property(object):
    """A property that is to be used in a bridged view model,
    inside JavaScript environment."""
    def __init__(self, property_type=_def_param_type):
        self.property_type = property_type

class BoundPropertyDescriptor(object):
    """A descriptor that emits specified by `signal_name` signal
    of an object to which it belongs every time the new value
    is set."""
    def __init__(self, signal_name):
        self.val = None
        self.signal_name = signal_name

    def __get__(self, obj, objtype):
        return self.val

    def __set__(self, obj, val):
        self.val = val
        getattr(obj, self.signal_name).emit(val)

def Event(*args, **kwa):
#    if len(args) == 0 and len(kwa) == 0:
#        return Event(object)

    return QtCore.Signal(*[_def_param_type if a == object else a for a in args], **kwa)

#Event = QtCore.Signal
receiver = QtCore.Slot(_def_param_type)

def bridged_view_model(cls):
    """Decorates a viewmodel class to be used in the JavaScript environment.
    For each BoundProperty attribute it:
    - replaces in with BoundPropertyDescriptor
    - adds a signal which is emitted every time the attribute value
    is changed
    - the signal name will be _sig_`attr_name`_changed"""
    def signal_name_for_prop(prop_name): return '_sig_%s_changed' % prop_name

    # add signal for each bound property
    attrs = {}
    for k, v in cls.__dict__.iteritems():
        if isinstance(v, Property):
            #print 'found a property: ', k
            # create a signal
            attrs[signal_name_for_prop(k)] = QtCore.Signal(v.property_type)
            # create a replacement attribute
            attrs[k] = BoundPropertyDescriptor(signal_name_for_prop(k))
        else: attrs[k] = v

    # add a QObject as a parent explicitly
    return type(cls.__name__, (QtCore.QObject,), attrs)

def _init_bridge_scripts(frame):
    """Adds bridge scripts to specified frame."""
    with open(os.path.join(os.path.dirname(__file__), 'bui.js'), 'r') as f:
        frame.evaluateJavaScript(f.read())

def _init_webview_frame(frame, viewmodels={}):
    """Adds viewmodel objects to JavaScript window object in
    specified `frame` and registers it with a call to
    bui.use_viewmodel().

    After this, the viewmodels are embedded in JS environment and
    have methods 'bind' and 'handle', which allow you to bind
    viewmodel properties and subscribe to viewmodel events."""
    def on_load():
        _init_bridge_scripts(frame)
        for k, v in viewmodels.iteritems():
            frame.addToJavaScriptWindowObject(k, v)
            frame.evaluateJavaScript('__.use_viewmodel(%s);' % k)

    frame.javaScriptWindowObjectCleared.connect(on_load)

def create_webview(view_url, viewmodels):
    """Creates a QWebView object ready to use with specified
    bridged viewmodels."""
    view = QtWebKit.QWebView()
    frame = view.page().currentFrame()
    view.load(QtCore.QUrl('file:///'+os.path.abspath(view_url).replace('\\', '/')))
    _init_webview_frame(frame, viewmodels)

    return view