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
from . import _
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.MenuList import MenuList
import skin



class duplicatesList(Screen):
	skin = """
		<screen name="duplicatesList" position="center,center" size="560,417" title="MovieManager - duplicates">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,40" zPosition="2" size="550,275" itemHeight="30" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,320" zPosition="2" size="550,2"/>
		<widget name="description" position="5,325" zPosition="2" size="550,92" valign="center" halign="left" font="Regular;20" foregroundColor="white"/>
	</screen>"""

	def __init__(self, session, duplicates):
		Screen.__init__(self, session)
		self.setTitle(_("MovieManager - List of possible duplicates"))

		self.skinName = ["duplicatesList", "Setup"]

		self.duplicates = duplicates
		self["key_red"] = Button(_("Cancel"))

		self.list = []
		self.reloadList()
		self["description"] = Label()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"red": self.exit,
			})

		text = _("Duplicates are detected based on the part of the title before the first comma ',' because some programs are re-broadcast with an additional phrase in the title. Therefore, some duplicates may not be actual duplicates.")
		self["description"].setText(text)

	def reloadList(self):
		for x in self.duplicates:
			self.list.append(x)

		self["config"] =  MenuList(self.list)

	def exit(self):
		self.close()
