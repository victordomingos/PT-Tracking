#!/usr/bin/env python3.6
# encoding: utf-8
"""
Este módulo é parte integrante da aplicação PT Tracking, desenvolvida por
Victor Domingos e distribuída sob os termos da licença Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

from tkinter import *
from tkinter import ttk


class AutocompleteEntry(ttk.Entry):
    """
    Subclass of tkinter.Entry that features autocompletion.
    To enable autocompletion use set_completion_list(list) to define
    a list of possible strings to hit.
    To cycle through hits use down and up arrow keys.

    Created by Mitja Martini on 2008-11-29.
    Converted to Python3 by Ian Weisser on 2014-04-06.
    Edited by Victor Domingos on 2016-04-25.

    https://gist.github.com/victordomingos/3a2a143c573e49308aad392acff25b47
    """

    def set_completion_list(self, completion_list):
        self._completion_list = completion_list
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        """autocomplete the Entry, delta may be 0/1/-1 to cycle through possible hits"""
        if delta: # need to delete selection otherwise we would fix the current position
            self.delete(self.position, END)
        else: # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits=_hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0, END)
            self.insert(0,self._hits[self._hit_index])
            self.select_range(self.position,END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            if self.position < self.index(END): # delete the selection
                self.delete(self.position, END)
            else:
                self.position = self.index(END)
        if event.keysym == "Left":
            if self.position < self.index(END): # delete the selection
                self.delete(self.position, END)
        if event.keysym == "Right":
            self.position = self.index(END) # go to end (no selection)
        if event.keysym == "Down":
            self.autocomplete(1) # cycle to next hit
        if event.keysym == "Up":
            self.autocomplete(-1) # cycle to previous hit
        # perform normal autocomplete if event is a single key
        if len(event.keysym) == 1:
            self.autocomplete()


class AutoScrollbar(Scrollbar):
    """
     a scrollbar that hides itself if it's not needed.  only
     works if you use the grid geometry manager.
     http://effbot.org/zone/tkinter-autoscrollbar.htm
    """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")


class NPKProgressBar(ttk.Frame):
    """ Simple Progress Bar class with custom methods.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.master = master
        self.progress_value = 0

        self.progress_bar = ttk.Progressbar(self,
                                            length=100,
                                            mode='indeterminate')

        self.place(in_=self.master, relx=1, rely=1, y=-10, anchor='e')


    def show_progress(self, max_value=100, value=0, length=100, mode='indeterminate'):
        """ Display a progress bar in the right side of the status bar. It
            can accept a different maximum value, if needed. Mode must be
            either "determinate" (it will display a real progress bar that
            can be updated), or "indeterminate" (it will display a simple
            progress bar that does not show a specific value.
        """
        self.progress_reset()
        self.progress_bar['mode'] = mode
        if length:
            self.progress_bar['length'] = length
        if mode == 'indeterminate':
            self.progress_bar.start()
        else:
            self.progress_bar['maximum'] = max_value
            self.progress_update(value)

        self.progress_bar.pack(side='right', padx="0 14")
        self.progress_bar.update()
        self.place(in_=self.master, relx=1, rely=1, y=-6, x=10, anchor='e')
        self.master.update()

    def _hide_progress(self):
        """ Do the actual hiding of the progress bar. """
        self.progress_bar.stop()
        self.place_forget()
        self.progress_reset()

    def hide_progress(self, last_update=None):
        """ Reset the progress bar and hide it. Optionaly, it can show
            momentaneously a final value, by providing a value to the
            last_update argument.
        """
        if last_update:
            self.progress_update(last_update)
            self.after(300, self._hide_progress)
        else:
            self._hide_progress()

    def progress_update(self, value):
        """ Make the progress bar advance by indicating its new value. """
        if value > self.progress_value:
            self.progress_value = value
            self.progress_bar['value'] = self.progress_value
            self.progress_bar.update()
            self.progress_bar.after(150, lambda: self.progress_update(self.progress_value+1))

    def progress_reset(self):
        """ Make the progress bar go back to zero. """
        self.progress_value = 0
        self.progress_bar['value'] = 0
        self.progress_bar.update()
