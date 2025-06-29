#
#  MovieManager
#
#
#  Coded by ims (c) 2018-2025
#  Support: openpli.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# for localized messages
from . import _, ngettext
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.MenuList import MenuList
from .ui import cfg
import os
import skin


class duplicatesList(Screen):
	skin = """
		<screen name="duplicatesList" position="center,center" size="560,417" title="MovieManager - duplicates">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,40" zPosition="2" size="550,275" itemHeight="30" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,320" zPosition="2" size="550,2"/>
		<widget name="description" position="5,325" zPosition="2" size="550,92" valign="center" halign="left" font="Regular;20" foregroundColor="white"/>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["duplicatesList", "Setup"]

		self.text = _(
				"Duplicates are detected based on the part of the title up to the selected comma ',' "
				"(because some programs are re-broadcast with an additional phrase in the title), "
				"or on the whole title. Therefore, some duplicates may not be actual duplicates."
		)
		self.comma = cfg.comma.value
		self["key_red"] = Button(_("Cancel"))
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["description"] = Label()

		self.list = []
		self["config"] =  MenuList(self.list)
		self.reloadList()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"red": self.exit,
				"yellow": self.prevCommaPosition,
				"blue": self.nextCommaPosition,
			})

	def setButtonsTexts(self):
		self["key_yellow"].setText(_("Less of title") if self.comma != 0 else "")
		self["key_blue"].setText(_("More of title") if self.comma != 3 else "")

	def commaTxt(self, comma_index=0):
		if comma_index == 3:
			return _("as whole titles")
		s = _("up to %s") % "...,...,...,"
		return s.replace(',', '[,]', 1 + comma_index).replace('[,]', ',', comma_index)

	def reloadList(self):
		self.list =  self.checkDuplicates(self.comma) or []
		self["config"].setList(self.list)
		self.setTitle(_("MovieManager - Duplicates (titles compared %s)") % self.commaTxt(self.comma))
		count = len(self.list)
		self["description"].setText(self.text + ngettext("\nFound %d possible duplicate.", "\nFound %d possible duplicates.", count) % count)
		self.setButtonsTexts()

	def prevCommaPosition(self):
		self.comma = max(self.comma - 1, 0)
		self.reloadList()

	def nextCommaPosition(self):
		self.comma = min(self.comma + 1, 3)
		self.reloadList()

	def find_latest_csv(self, directory):
		try:
			files = [f for f in os.listdir(directory) if f.startswith("movies-") and f.endswith(".csv") and os.path.isfile(os.path.join(directory, f))]
			if files:
				latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
				latest_file_name = latest_file
			else:
				latest_file_name = None
			return latest_file_name
		except Exception as e:
			print("ERROR while searching for the file:", e)
			return None

	def checkDuplicates(self, comma_index=0):
		filename = self.find_latest_csv(cfg.csvtarget.value)
		if filename is None:
			self.MessageBoxNM("The CSV file does not exist or the path is not set correctly!", 5)
			return
		filename = os.path.join(cfg.csvtarget.value, filename)

		duplicates = []
		prev_key = None
		group = []

		with open(filename, encoding='utf-8') as f:
			for i, line in enumerate(f):
				if i == 0:
					continue  # skip header

				line = line.strip()
				full_name = line.split(';', 1)[0].strip()

				parts = full_name.split(',')
				if comma_index != 3 and comma_index < len(parts):
					key = ','.join(parts[:comma_index + 1]).strip().lower()
				else:
					key = full_name.strip().lower()

				if key != prev_key:
					if len(group) > 1:
						duplicates.extend(group)
					group = [line]
					prev_key = key
				else:
					group.append(line)

			# last group
			if len(group) > 1:
				duplicates.extend(group)

		return duplicates

	def exit(self):
		cfg.comma.value = self.comma
		cfg.comma.save()
		self.close()
