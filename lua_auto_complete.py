# This Python file uses the following encoding: utf-8
#-----------------------------------------------------------------------------------
# Lua Functions Auto Complete
#-----------------------------------------------------------------------------------
#
# This plug-in adds auto-completion entries from the WRP-lua file.
#
# (c) Jory Liang
#-----------------------------------------------------------------------------------
import sublime
import sublime_plugin

from WDMLMarkup.scanner import scan_folders

ST3 = int(sublime.version()) > 3000

import os
import re

class LuaAutoComplete(sublime_plugin.EventListener):
    b_first_edit = True
    b_fully_loaded = True
    path_list = []
    word_list = {}

    # on first modification in comments, get the dictionary and save items.
    def on_post_save_async(self, view):
        if self.b_first_edit or self.b_fully_loaded:
            self.b_fully_loaded = False
            sublime.set_timeout(lambda: self.load_completions(view), 3)
    def on_activated(self, view):
        if self.b_first_edit or self.b_fully_loaded:
            self.b_fully_loaded = False
            sublime.set_timeout(lambda: self.load_completions(view), 3)

    def load_completions(self, view):
        scope_name = view.scope_name(view.sel()[0].begin())       # sublime.windows()[0].active_view()
        if self.should_trigger(scope_name):
            self.path_list = []
            self.word_list = []
            default_path = sublime.load_settings('WDMLMarkup.sublime-settings').get('default_library_path')
            load_opened_folder = sublime.load_settings('WDMLMarkup.sublime-settings').get('load_opened_folder')
            self.path_list.extend(default_path)
            if load_opened_folder == "true":
                for w in sublime.windows():
                    self.path_list.extend(w.folders())

            self.word_list = scan_folders(self.path_list)
            self.b_fully_loaded = True
        else:
            print("no trigger")
            self.b_fully_loaded = True

    # This will return all words found in the dictionary.
    def get_autocomplete_list(self, word):
        print("get_autocomplete_list")
        autocomplete_list = []
        # filter relevant items:
        for w in self.word_list:
            try:
                if word[0].islower():
                    return autocomplete_list
                if word.lower() in w.lower():
                    W = self.init_cursor(w)
                    autocomplete_list.append((w, W))
            except UnicodeDecodeError:
                print(w)
                # autocomplete_list.append((w, w))
                continue

        return autocomplete_list

    def init_cursor(self, word):
    # return re.sub(r'(\w+)([,\)])', r'${:\1}\2', word)
        func_body = re.split(r'\s*[,\(\)]\s*', word)
        index = 0
        new_word = ""
        for item in func_body:
            if index == 0:  
                new_word = item + "("
            elif item == "":
                new_word = new_word[:-2] + ")"
            else:
                new_word += "${" + str(index) + ":" + item + "}, "
            index += 1
        return new_word

    def should_trigger(self, scope):
        print(scope)
        if "source.lua" in scope or "text.wdml" in scope:
            return True
        return False

    # gets called when auto-completion pops up.
    def on_query_completions(self, view, prefix, locations):
        print("on_query_completions")
        scope_name = sublime.active_window().active_view().scope_name(sublime.active_window().active_view().sel()[0].begin())
        if self.should_trigger(scope_name):
            return self.get_autocomplete_list(prefix)
