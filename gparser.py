#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Graphical interface for the morphological parser
#
# Copyright (C) 2010  Kirill Maslinsky <kirill@altlinux.org>
#
# This file is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#

import wx
import os
import mparser
from contextlib import contextmanager

class FilePanel(wx.Panel):
    'Text fileview panel'
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(self.control, 1, wx.EXPAND)
        self.SetSizer(Sizer)
        self.SetAutoLayout(1)

class DictionaryItem(wx.Panel):
    def __init__(self, parent, dictloader, dictid, b_id, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        (lang, name) = dictid
        ((ver,sha), dic) = dictloader.dictlist[(lang, name)]
        hbox.Add(wx.StaticText(self, -1, '\t'.join([lang, name, ver])),0)
        rbutton = wx.Button(self, b_id, "Remove")
        self.Bind(wx.EVT_BUTTON, parent.OnRemove, rbutton)
        hbox.Add(rbutton,0)
        self.SetSizer(hbox)
        self.Layout()


class DictionaryLister(wx.Panel):
    def __init__(self, parent, dictloader, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.buttons = {}
        self.children = {}
        self.parent = parent
        self.dictloader = dictloader
        dictbox = wx.StaticBox(self, -1, "Available Dictionaries")
        self.dsizer = wx.StaticBoxSizer(dictbox, wx.VERTICAL)
        b_id = 0
        for (lang, name), ((ver, sha), dic) in self.dictloader.dictlist.iteritems():
            b_id = b_id + 10
            self.buttons[b_id] = (lang, name)
            d_item = DictionaryItem(self, self.dictloader, (lang, name), b_id)
            self.children[(lang, name)] = d_item
            self.dsizer.Add(d_item,0, wx.TOP|wx.LEFT,10)
        abutton = wx.Button(self, -1, "Add dictionary")
        self.Bind(wx.EVT_BUTTON, self.OnAdd, abutton)
        self.dsizer.Add(abutton,0,wx.TOP|wx.LEFT,10)
        self.SetSizer(self.dsizer)
        self.Layout()

    def OnRemove(self, evt):
        dictid = self.buttons[evt.GetId()]
        self.dictloader.remove(dictid)
        self.GetTopLevelParent().processor.update()
        c_id = self.children[dictid]
        self.dsizer.Detach(c_id)
        c_id.Show(False)
        del self.buttons[evt.GetId()]
        del self.children[dictid]
        self.dsizer.Layout()
        
        
    def OnAdd(self, evt):
        dlg = wx.FileDialog(self, message="Select dictionary file", wildcard="Toolbox dict (*.txt)|*.txt", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            dictfile = dlg.GetPath()
            (lang, name) = self.dictloader.add(dictfile)
            if lang is None:
                return
            self.GetTopLevelParent().processor.update()
            if not (lang, name) in self.children:
                ((ver,sha), dic) = self.dictloader.dictlist[(lang, name)]
                try:
                    b_id = max(self.buttons.keys())+10
                except (ValueError):
                    b_id = 10
                self.buttons[b_id] = (lang, name)
                d_item = DictionaryItem(self, self.dictloader, (lang, name), b_id)
                self.children[(lang,name)] = d_item
                self.dsizer.Insert(0, d_item, 0, wx.TOP|wx.LEFT,10)
                self.dsizer.Layout()
                self.Refresh()


class GrammarLister(wx.Panel):
    def __init__(self, parent, grammarloader, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.grammarloader = grammarloader
        grambox = wx.StaticBox(self, -1, "Available Grammar")
        self.gsizer = wx.StaticBoxSizer(grambox, wx.VERTICAL)
        self.gramlist = wx.StaticText(self, -1, '\n'.join(self.grammarloader.gramlist))
        self.gsizer.Add(self.gramlist, 0, wx.TOP|wx.LEFT, 10)
        gbutton = wx.Button(self, -1, "(Re)Load grammar")
        self.gsizer.Add(gbutton, 0, wx.TOP|wx.LEFT, 10)
        self.Bind(wx.EVT_BUTTON, self.OnLoad, gbutton)
        self.SetSizer(self.gsizer)
        self.Layout()

    def OnLoad(self, evt):
        dlg = wx.FileDialog(self, message="Select grammar file", wildcard="Mparser grammar (*.txt)|*.txt", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            gramfile = dlg.GetPath()
            self.grammarloader.load(gramfile)
            self.GetTopLevelParent().processor.update()
            oldname = self.gramlist
            oldname.Show(False)
            self.gramlist = wx.StaticText(self, -1, '\n'.join(self.grammarloader.gramlist))
            self.gsizer.Replace(oldname, self.gramlist)
            self.gramlist.Show(True)
            self.Layout()

class ResourcePanel(wx.Panel):
    def __init__(self, parent, dictloader, grammarloader, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        Sizer = wx.BoxSizer(wx.VERTICAL)
        dictlist = DictionaryLister(self, dictloader)
        Sizer.Add(dictlist, 1, wx.EXPAND)
         
        gramlist = GrammarLister(self, grammarloader)
        Sizer.Add(gramlist, 1, wx.EXPAND)

        self.SetSizer(Sizer)
        self.SetAutoLayout(1)
        
class MainFrame(wx.Frame):
    'Main frame'
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)

        # setup Processor
        dl = mparser.DictLoader()
        gr = mparser.GrammarLoader()

        self.dirname = os.curdir
        self.infile = None
        self.outfile = None
        
        self.filepanel = FilePanel(self)
        self.resourcepanel = ResourcePanel(self, dl, gr)


        self.processor = mparser.Processor(dl, gr)

        filemenu= wx.Menu()
        menuOpen = filemenu.Append(wx.ID_OPEN,"O&pen"," Open text file")
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        menuSave = filemenu.Append(wx.ID_SAVE,"S&ave"," Save an xhtml file")
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)
        menuSaveAs = filemenu.Append(wx.ID_SAVEAS,"S&ave as"," Save an xhtml file")
        self.Bind(wx.EVT_MENU, self.OnSaveAs, menuSaveAs)
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        

        Sizer = wx.BoxSizer(wx.HORIZONTAL)
        Sizer.Add(self.filepanel, 2, wx.EXPAND)
        Sizer.Add(self.resourcepanel, 1, wx.EXPAND)
        self.SetSizer(Sizer)
        self.SetAutoLayout(1)
        self.Fit()


    def OnParse(self,e):
        @contextmanager
        def wait_for_parser():
            yield self.processor.parse()

        dlg = wx.MessageDialog(self, 'Please wait: parsing in progress', 'Please wait', wx.OK)
        dlg.ShowModal()

        with wait_for_parser():
            dlg.Destroy()
            self.FinishedParsing(e)

    def NoFileError(self,e):
        dlg = wx.MessageDialog(self, 'Error: no file opened!', 'No file opened', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def FinishedParsing(self,e):
        dlg = wx.MessageDialog(self, 'Parsing finished successfully', 'Parsing finished successfully', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self,e):
        self.Close(True)

    def OnOpen(self,e):
        """ Open a file"""
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.infile = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            self.processor.read_file(self.infile)
            self.filepanel.control.SetValue('\n\n'.join(self.processor.txt))
        dlg.Destroy()

    def OnSave(self,e):
        if not self.infile:
            self.NoFileError(e)
        if not self.outfile:
            self.OnSaveAs(e)
        else:
            self.OnParse(e)
            self.processor.write(self.outfile)

    def OnSaveAs(self,e):
        if not self.infile:
            self.NoFileError(e)
        else:
            xfilename = '.'.join([os.path.splitext(self.infile)[0], 'parsed'])

            dlg = wx.FileDialog(self, "Choose a file", os.path.dirname(self.infile), xfilename, "*.html", wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                self.outfile = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
                if not os.path.splitext(self.outfile)[1] == '.html' :
                    self.outfile = ''.join([self.outfile, os.path.extsep, 'html'])
                    self.OnParse(e)
                    self.processor.write(self.outfile)
            dlg.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None, title="Bamana morphological parser (GUI)")
    frame.Show()
    app.MainLoop()
