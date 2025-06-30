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
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config
from Components.MenuList import MenuList
from .ui import cfg
import skin


class duplicatesList(Screen, HelpableScreen):
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

	def __init__(self, session, filename):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["duplicatesList", "Setup"]

		self.text = _(
				"Duplicates are detected based on the part of the title up to the selected comma ',' "
				"(because some programs are re-broadcast with an additional phrase in the title), "
				"or on the whole title. Therefore, some duplicates may not be actual duplicates."
		)
		self.comma = cfg.comma.value
		self.filename = filename
		self["key_red"] = Button(_("Cancel"))
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["description"] = Label()

		self.list = []
		self["config"] =  MenuList(self.list)
		self.reloadList()

		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions"],
			{
				"cancel": (self.exit, _("Close the window with duplicates")),
				"red": (self.exit, _("Close the window with duplicates")),
				"yellow": (self.prevCommaPosition , _("Shorter part of title (earlier comma) for comparison")),
				"blue": (self.nextCommaPosition, _("Longer part of title (later comma or full) for comparison")),
				"ok": (self.info, _("Shows and hides info for the selected item")),
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
		self.list =  self.checkDuplicates(self.filename, self.comma) or []
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

	def checkDuplicates(self, filename, comma_index=0):
		duplicates = []
		prev_key = None
		group = []

		with open(filename, encoding='utf-8') as f:
			for i, line in enumerate(f):
				if i == 0:
					self.header = line.split(';')
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

	def info(self):
		item = self["config"].getCurrent()
		if item:
			par = item.split(";")
			if len(par) == 7 and len(self.header) == 7:
				text = "\n%s\n\n" % par[0]
				text += "%s\t%s %s\n" % (_("Size:"), par[1], self.header[1].split("[")[1].split("]")[0])
				text += "%s\t%s\n" % (_("Duration:"), par[2])
				text += "%s\t%s\n" % (_("Location:"), par[3])
				text += "%s\t%s\n" % (_("Service:"), par[4])
				text += "%s\t%s, %s\n" % (_("Recorded:"), ".".join(par[5].split(".")[::-1]), par[6])
			else:
				text = item
			self.session.open(MessageBox, text, type=MessageBox.TYPE_MESSAGE, simple=True)

	def exit(self):
		cfg.comma.value = self.comma
		cfg.comma.save()
		self.close()
