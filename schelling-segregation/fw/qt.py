#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 3/28/12
@author: eis
"""
try:
    from PySide import QtCore, QtGui, QtWebKit
except ImportError:
    try:
        from PyQt4 import QtCore, QtGui, QtWebKit
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot
    except ImportError:
        raise Exception("Can't import PyQt or PySide.")

__all__ = ['QtCore', 'QtGui', 'QtWebKit']
