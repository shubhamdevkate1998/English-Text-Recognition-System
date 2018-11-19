#!/usr/bin/env python3
###########################################################################
#    Lios - Linux-Intelligent-Ocr-Solution
#    Copyright (C) 2011-2015 Nalin.x.Linux GPL-3
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

from lios.ui.gtk import text_view, widget, dialog, file_chooser, containers, window

from lios.text_to_audio import text_to_audio_converter
from lios import macros
from lios import dictionary
from lios import localization
from lios.ui.gtk import print_dialog

import queue

_ = localization._

class BasicTextView(text_view.TextView):
	def __init__(self):
		super(BasicTextView,self).__init__()
		self.q = queue.LifoQueue()
		self.q2 = queue.LifoQueue()
		self.connect_insert(self.push)
		self.connect_delete(self.push)
		
		#This variable is to avoid the reverse event 
		#while pressing undo or redo that again trigger
		# insert or delete signals - Nalin.x.GNU
		self.push_change_to_undobuffer = True;
	
	def set_dictionary(self,dict):
		self.dict = dict
	
	def undo(self,arg=None):
		if( not self.q.empty()):
			text = self.q.get()
			self.push_change_to_undobuffer = False
			self.set_text(text)
			self.q2.put(text)
		
	def redo(self,arg=None):
		if( not self.q2.empty()):
			text = self.q2.get()
			self.push_change_to_undobuffer = False
			self.set_text(text)
			self.q.put(text)
	
	def push(self):
		text = self.get_text()
		if(text and self.push_change_to_undobuffer):
			self.q.put(text)
		else:
			self.push_change_to_undobuffer = True


	def new(self,*data):
		if (self.get_modified() == True):
			dlg =  dialog.Dialog(_("Start new without saving ?"),
			("Cancel", dialog.Dialog.BUTTON_ID_1,_("Start-New!"), dialog.Dialog.BUTTON_ID_2))                           						
			label = widget.Label(_("Start new without saving ?"))
			dlg.add_widget(label)
			label.show()
			response = dlg.run()
			dlg.destroy()				
			if response == dialog.Dialog.BUTTON_ID_1:
				self.grab_focus();
				return 0;
			else:
				self.delete_all_text()
				self.grab_focus();
				return 1;
		else:
			self.delete_all_text()
			return 1;

	def open(self):
		open_file = file_chooser.FileChooserDialog(_("Select the file to open"),
			file_chooser.FileChooserDialog.OPEN,
			macros.supported_text_formats,macros.home_dir)
		response = open_file.run()
		if response == file_chooser.FileChooserDialog.ACCEPT:
			to_read = open("%s" % (open_file.get_filename()))
			to_open = to_read.read()
			try:
				self.set_text(to_open)
			except FileNotFoundError:
					pass
			else:
				self.save_file_name = open_file.get_filename()
				#self.textbuffer.place_cursor(self.textbuffer.get_end_iter())
		open_file.destroy()

	def save(self,*data):
		text = self.get_text()
		try:
			self.save_file_name
		except AttributeError:
			save_file = file_chooser.FileChooserDialog(_("Save "),
				file_chooser.FileChooserDialog.SAVE,
				macros.supported_text_formats,None)
			save_file.set_current_name(text[0:10]);
			save_file.set_do_overwrite_confirmation(True);			
			response = save_file.run()
			if response == file_chooser.FileChooserDialog.ACCEPT:
				self.save_file_name = save_file.get_filename()
				open("%s" %(self.save_file_name),'w').write(text)
				self.set_modified(False)	
				save_file.destroy()
				return True
			else:
				save_file.destroy()
				return False
		else:
			open(self.save_file_name,'w').write(text)
			self.set_modified(False)
			return True		


	def save_as(self,*data):
		try:
			del self.save_file_name
		except:
			pass
		self.save();
		
	def append(self,*data):
		append_file_dialog = file_chooser.FileChooserDialog(_("Select the file to append"),
			file_chooser.FileChooserDialog.OPEN,macros.supported_text_formats)
		append_file_dialog.set_current_folder("~/")
		append_file_dialog.run()
		with open(append_file_dialog.get_filename()) as file:
			text_to_append = file.read()
			self.insert_text(text_to_append,2,True)
		append_file_dialog.destroy()
	
	def punch(self,*data):
		insert_at_cursor_dialog = file_chooser.FileChooserDialog(_("Select the file to insert at cursor"),
			file_chooser.FileChooserDialog.OPEN,macros.supported_text_formats)
		insert_at_cursor_dialog.set_current_folder("~/")
		insert_at_cursor_dialog.run()
		with open(insert_at_cursor_dialog.get_filename()) as file:
			text_to_insert_at_cursor = file.read()
			self.insert_text(text_to_insert_at_cursor,1,True)
		insert_at_cursor_dialog.destroy()
		
	
	def open_find_dialog(self,*data):
		entry = widget.Entry()
		statusbar_context = widget.Statusbar()
		statusbar_context.set_text(_("Context label"))

		def find_next(*data):
			word = entry.get_text()
			if(not self.is_cursor_at_end()):
				if(self.move_forward_to_word(word)):
					statusbar_context.set_text(self.get_context_text())

		def find_previous(*data):
			word = entry.get_text()
			if(not self.is_cursor_at_start()):
				if(self.move_backward_to_word(word)):
					statusbar_context.set_text(self.get_context_text())
			
		label = widget.Label(_("<b> Find word  : </b>"))
		label.set_use_markup(True)
		label.set_mnemonic_widget(entry)
		
		next_button = widget.Button(_("Next"))
		next_button.connect_function(find_next)	
		previous_button = widget.Button(_("Previous"))
		previous_button.connect_function(find_previous)
		
		
		grid = containers.Grid()
		grid.add_widgets([(label,1,1),(entry,1,1),containers.Grid.NEW_ROW,
			(statusbar_context,2,1),containers.Grid.NEW_ROW,(next_button,1,1,False,False),
			(previous_button,1,1,False,False)])
		window_find = window.Window(_("Find Dialog"))
		window_find.add(grid)
		window_find.show_all()

	def open_find_and_replace_dialog(self,*data):
		entry_word = widget.Entry()
		entry_replace_word = widget.Entry()
		statusbar_context = widget.Statusbar()
		statusbar_context.set_text(_("Context label"))

		def find_next(*data):
			word = entry_word.get_text()
			if(not self.is_cursor_at_end()):
				if(self.move_forward_to_word(word)):
					statusbar_context.set_text(self.get_context_text())

		def find_previous(*data):
			word = entry_word.get_text()
			if(not self.is_cursor_at_start()):
				if(self.move_backward_to_word(word)):
					statusbar_context.set_text(self.get_context_text())
				else:
					dialog.Dialog(_("No match found")).run()

		def replace(*data):
			word_replace = entry_replace_word.get_text()
			self.replace_last_word(word_replace)

		def replace_all(*data):
			word = entry_word.get_text()
			word_replace = entry_replace_word.get_text()
			while(not self.is_cursor_at_end()):
				if(self.move_forward_to_word(word)):
					self.replace_last_word(word_replace)
				else:
					break
			
		label_word = widget.Label(_("<b> word  : </b>"))
		label_word.set_use_markup(True)
		label_word.set_mnemonic_widget(entry_word)
		label_replace_word = widget.Label(_("<b> Replace word : </b>"))
		label_replace_word.set_use_markup(True)
		label_replace_word.set_mnemonic_widget(entry_replace_word)
		
		button_next = widget.Button(_("Next"))
		button_next.connect_function(find_next)	
		button_previous = widget.Button(_("Previous"))
		button_previous.connect_function(find_previous)
		button_replace = widget.Button(_("Replace"))
		button_replace.connect_function(replace)	
		button_replace_all = widget.Button(_("Replace-All"))
		button_replace_all.connect_function(replace_all)
		
		
		grid = containers.Grid()
		grid.add_widgets([(label_word,2,1),(entry_word,4,1),containers.Grid.NEW_ROW,
			(label_replace_word,2,1),(entry_replace_word,4,1),containers.Grid.NEW_ROW,
			(button_next,3,1,False,False),(button_previous,3,1,False,False),
			containers.Grid.NEW_ROW,(statusbar_context,6,1),containers.Grid.NEW_ROW,
			(button_replace,3,1,False,False),(button_replace_all,3,1,False,False)])
		window_find = window.Window(_("Find Dialog"))
		window_find.add(grid)
		window_find.show_all()
	
	def open_spell_check(self,*data):
		entry = widget.Entry()
		list_view = widget.ListView(_("Suggestions"))
		statusbar_context = widget.Statusbar()
		statusbar_context.set_text(_("Context label"))
		statusbar_context.set_line_wrap(True)
		change_all_dict = {}
		self.word = ""


		def find_next_mispeleed_word(*data):
			while (not self.is_cursor_at_end()):
				self.word = self.get_next_word()
				if self.word in change_all_dict.keys():
					self.replace_last_word(change_all_dict[self.word])
					continue
					
				if (not self.dict.check(self.word)):
					entry.set_text(self.word)
					statusbar_context.set_text(self.get_context_text())
					list_view.clear()
					for item in self.dict.suggest(self.word):
						list_view.add_item(item)
					break
			if(self.is_cursor_at_end()):
				entry.set_text("")
				statusbar_context.set_text("Spell Check finished")
			

		def ignore_all(*data):
			word = entry.get_text()
			self.dict.add_to_session(word)
			find_next_mispeleed_word()
		
		def change(*data):
			replace_word = entry.get_text()
			self.replace_last_word(replace_word)
			find_next_mispeleed_word()
		
		def change_all(*data):
			replace_word = entry.get_text()
			change_all_dict[self.word] = replace_word
			self.replace_last_word(replace_word)
			print(change_all_dict)
			find_next_mispeleed_word()
		
		def delete(*data):
			self.delete_last_word()
			find_next_mispeleed_word()
		
		def on_suggestion_selected(*data):
			item = list_view.get_selected_item()
			entry.set_text(item)
		
		def close(*data):
			window1.destroy()	
		
		grid = containers.Grid()
		
		label = widget.Label(_("<b> Misspelled word  : </b>"))
		label.set_use_markup(True)
		label.set_mnemonic_widget(entry)
		
		scroll_box = containers.ScrollBox()
		scroll_box.add(list_view)
		change_button = widget.Button(_("Change"))
		change_button.connect_function(change)
		change_all_button = widget.Button(_("Change All"))
		change_all_button.connect_function(change_all)
		delete_button = widget.Button(_("Delete"))
		delete_button.connect_function(delete)
		ignore_button = widget.Button(_("Ignore"))
		ignore_button.connect_function(find_next_mispeleed_word)
		ignore_all_button = widget.Button(_("Ignore All"))
		ignore_all_button.connect_function(ignore_all)
		add_to_dict_button = widget.Button(_("Add to user dict"))
		close_button = widget.Button(_("Close"))
		close_button.connect_function(close)
		
		list_view.connect_on_select_callback(on_suggestion_selected)
				
		grid.add_widgets([(label,1,1,False,False),
			(entry,6,1,False,False),containers.Grid.NEW_ROW,
			(scroll_box,1,3,False,False),(change_button,1,1,False,False),(change_all_button,1,1,False,False),(delete_button,1,1,False,False),containers.Grid.NEW_ROW,
			(ignore_button,1,1,False,False),(ignore_all_button,1,1,False,False),(add_to_dict_button,1,1,False,False),containers.Grid.NEW_ROW,
			(statusbar_context,1,1),containers.Grid.NEW_ROW,
			(close_button,4,1,False,False)])
		
		find_next_mispeleed_word()
		
		window1 = window.Window(_("Spell-Check"))
		window1.add(grid)
		window1.set_default_size(500,200)
		window1.show_all()

	
	def go_to_line(self,*data):
		current_line = self.get_cursor_line_number()
		maximum_line = self.get_line_count()		
		spinbutton_line = widget.SpinButton(current_line,0,maximum_line,1,5,0)
		
		dlg = dialog.Dialog(_("Go to line"),(_("Go"), dialog.Dialog.BUTTON_ID_1,_("Close!"), dialog.Dialog.BUTTON_ID_2))
		#spinbutton_line.connect("activate",lambda x : dialog.response(Gtk.ResponseType.ACCEPT))
		dlg.add_widget_with_label(spinbutton_line,_("Line Number : "))
		spinbutton_line.grab_focus()
		dlg.show_all()
		response = dlg.run()
		
		if response == dialog.Dialog.BUTTON_ID_1:
			to = spinbutton_line.get_value()
			self.move_cursor_to_line(to)
			dlg.destroy()
		else:
			dlg.destroy()
	
	def audio_converter(self,data=None):
		if (self.has_selection()):
			text = self.get_selected_text()
		else:
			text = self.get_text()
		
		dialog_ac = dialog.Dialog(_("Audio converter "),(_("Convert"), dialog.Dialog.BUTTON_ID_1,_("Close!"), dialog.Dialog.BUTTON_ID_2))
		grid = containers.Grid()

		spinbutton_speed = widget.SpinButton(50,0,100,1,5,0)
		label_speed = widget.Label(_("Speed : "))
		label_speed.set_mnemonic_widget(spinbutton_speed)

		spinbutton_volume = widget.SpinButton(100,0,100,1,5,0)
		label_volume = widget.Label(_("Volume : "))
		label_volume.set_mnemonic_widget(spinbutton_volume)

		spinbutton_pitch = widget.SpinButton(50,0,100,1,5,0)
		label_pitch = widget.Label(_("Pitch : "))
		label_pitch.set_mnemonic_widget(spinbutton_pitch)

		spinbutton_split = widget.SpinButton(5,0,100,1,5,0)
		label_split_time = widget.Label(_("Split Time : "))
		label_split_time.set_mnemonic_widget(spinbutton_split)
		
		combobox = widget.ComboBox()
		for item in text_to_audio_converter.list_voices():
			combobox.append_text(item)
		label_voice = widget.Label(_("Voice : "))
		label_voice.set_mnemonic_widget(combobox)
		
		grid.add_widgets([
			(label_speed,1,1),(spinbutton_speed,1,1),containers.Grid.NEW_ROW,
			(label_volume,1,1),(spinbutton_volume,1,1),containers.Grid.NEW_ROW,
			(label_pitch,1,1),(spinbutton_pitch,1,1),containers.Grid.NEW_ROW,
			(label_split_time,1,1),(spinbutton_split,1,1),containers.Grid.NEW_ROW,
			(label_voice,1,1),(combobox,1,1)])
		dialog_ac.add_widget(grid)
		grid.show_all()
		
		if (dialog_ac.run() == dialog.Dialog.BUTTON_ID_1):
			speed = spinbutton_speed.get_value()
			pitch = spinbutton_pitch.get_value()
			volume = spinbutton_volume.get_value()
			split = spinbutton_split.get_value()
			voice = combobox.get_active_text()
			save_file = file_chooser.FileChooserDialog(_("Select the file to open"),file_chooser.FileChooserDialog.SAVE,["wav"],macros.home_dir)
			response = save_file.run()
			if response == file_chooser.FileChooserDialog.ACCEPT:
				converter = text_to_audio_converter(text,volume,voice,split,pitch,speed)
				converter.record_to_wave(save_file.get_filename())
			save_file.destroy()
		dialog_ac.destroy()
		
				

	def print_preview(self,*data):
		if (self.has_selection()):
			text = self.get_selected_text()
		else:
			text = self.get_text()
		print_dialog.print_with_action(text,print_dialog.print_with_action.PREVIEW)
			
	def open_print_dialog(self,*data):
		if (self.has_selection()):
			text = self.get_selected_text()
		else:
			text = self.get_text()
		print_dialog.print_with_action(text,print_dialog.print_with_action.PRINT_DIALOG)		
		
	def print_to_pdf(self,*data):
		save_file = file_chooser.FileChooserDialog(_("Enter the file name"),
			file_chooser.FileChooserDialog.SAVE,macros.supported_pdf_formats,macros.home_dir)
		response = save_file.run()
		if response == file_chooser.FileChooserDialog.ACCEPT:
			if (self.has_selection()):
				text = self.get_selected_text()
			else:
				text = self.get_text()
			print_dialog.print_with_action(text,print_dialog.print_with_action.EXPORT,
				save_file.get_filename())
			save_file.destroy()
