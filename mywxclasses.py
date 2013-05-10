#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  mywxclasses.py, version 0.1
#  
#  Copyright 2012 Bart De Vries <devries.bart@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
import wx
import wx.lib.mixins.listctrl as listmix


class TextEditVetoMixin(listmix.TextEditMixin):
    def __init__(self, vetocols=[]):
        listmix.TextEditMixin.__init__(self)
        self.vetocols = vetocols
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self._OnBeginLabelEdit)

    def _OnBeginLabelEdit(self, e):
        if e.m_col in self.vetocols:
            e.Veto()
        else:
            e.Skip()


class TextEditUpperMixin(listmix.TextEditMixin):
    def __init__(self):
        listmix.TextEditMixin.__init__(self)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._OnEndLabelEdit)

    def _OnEndLabelEdit(self, e):
        index = e.GetIndex()
        col = e.GetColumn()
        text = e.GetLabel().upper()
        self.SetStringItem(index, col, text)
        e.Veto()


class DeleteListItemMixin(object):
    def __init__(self, vetorows=[]):
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyPressed, self)
        self.delvetofromend = []
        self.delveto = []
        for i in vetorows:
            if i < 0:
                self.delvetofromend.append(i)
            else:
                self.delveto.append(i)

    def getselecteditems(self):
        """    
        Gets the selected items for the list control.
        Selection is returned as a list of selected indices,
        low to high.
        """
        veto = self.delveto + [max(self.GetItemCount()+i,0) for i in self.delvetofromend]
        selection = []
        index = self.GetFirstSelected()
        if index == -1 or index in veto:
            return []
        selection.append(index)
        while len(selection) != self.GetSelectedItemCount():
            index = self.GetNextSelected(index)
            if index != self.GetItemCount()-1:
                selection.append(index)
        selection.sort(reverse=True)
        return selection
    
    def removeselected(self):
        selection = self.getselecteditems()
        for i in selection:
            self.DeleteItem(i)

    def OnKeyPressed(self, e):
        keycode = e.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self.removeselected()


class TextEditDeleteEmptyMixin(listmix.TextEditMixin):
    def __init__(self, vetorows=[]):
        listmix.TextEditMixin.__init__(self)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._OnEndLabelEditDelete)
        self.remveto = []
        self.remvetofromend = []
        for i in vetorows:
            if i < 0:
                self.remvetofromend.append(i)
            else:
                self.remveto.append(i)

    def _OnEndLabelEditDelete(self, e):
        veto = self.remveto + [max(self.GetItemCount()+i,0) for i in self.remvetofromend]
        row = e.GetIndex()
        col = e.GetColumn()
        tempstr = e.GetText()
        for i in xrange(self.GetColumnCount()):
            if i == col:
                continue
            tempstr += self.GetItem(row, i).GetText()
        if not tempstr and not (row in veto):
            self.DeleteItem(row)
            e.Veto()
        else:
            e.Skip()


class DragListItemMixin(object):
    def __init__(self, vetorows=[]):
        self.Bind(wx.EVT_LEFT_DOWN, self.OnBeginDrag)
        self.Bind(wx.EVT_LEFT_UP, self.OnEndDrag)        
        self.startdragindex = -1
        self.dragvetofromend = []
        self.dragveto = []
        for i in vetorows:
            if i < 0:
                self.dragvetofromend.append(i)
            else:
                self.dragveto.append(i)

    def OnBeginDrag(self, e):
        index, flag = self.HitTest(e.GetPosition())
        veto = self.dragveto + [max(self.GetItemCount()+i,0) for i in self.dragvetofromend]
        if index != -1 and not (index in veto):
            self.startdragindex = index 
        e.Skip()
                   
    def OnEndDrag(self, e):
        index, flag = self.HitTest(e.GetPosition())
        veto = self.dragveto + [max(self.GetItemCount()+i,0) for i in self.dragvetofromend]
        if index != -1 and self.startdragindex != -1:
            if not (index in veto) and not (index == self.startdragindex):
                self._moverow(self.startdragindex, index)
        self.startdragindex = -1
        e.Skip()

    def _moverow(self, index1, index2):
        tempitem = [self.GetItem(index1)]
        tempitem[0].SetId(index2)
        for i in xrange(1, self.GetColumnCount()):
            tempitem.append(self.GetItem(index1, i).GetText())
        self.DeleteItem(index1)
        self.InsertItem(tempitem[0])
        for i in xrange(1, self.GetColumnCount()):   
            self.SetStringItem(index2, i, tempitem[i])


class DragEditListItemMixin(listmix.TextEditMixin, DragListItemMixin):
    def __init__(self, vetorows=[]):
        listmix.TextEditMixin.__init__(self)
        DragListItemMixin.__init__(self, vetorows)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self._OnBeginLabelEditDrag)

    def _OnBeginLabelEditDrag(self, e):
        self.startdragindex = -1
        e.Skip()

class EditListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   TextEditVetoMixin,
                   TextEditUpperMixin):
    """
    Custom ListCtrl which allows editing and autowidth resizing of 
    columns.  By default, all columns are editable, but through a 
    list/tuple argument vetocols, one can specify which columns should 
    not be editable.
    """
    editorBgColour = wx.Colour(255,255,255) # White

    def __init__(self, parent, vetocols=[], *args, **kwargs):
        wx.ListCtrl.__init__(self, parent, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        TextEditVetoMixin.__init__(self, vetocols)
        TextEditUpperMixin.__init__(self)



class AddListCtrl(wx.ListCtrl,
                  listmix.ListCtrlAutoWidthMixin,
                  TextEditDeleteEmptyMixin,
                  TextEditUpperMixin,
                  DragEditListItemMixin,
                  DeleteListItemMixin):
    
    editorBgColour = wx.Colour(255,255,255) # White

    def __init__(self, parent, vetocols=[], *args, **kwargs):
        wx.ListCtrl.__init__(self, parent, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        TextEditUpperMixin.__init__(self)
        TextEditDeleteEmptyMixin.__init__(self, vetorows=[-1])
        DragEditListItemMixin.__init__(self, vetorows=[-1])
        DeleteListItemMixin.__init__(self, vetorows=[-1])



