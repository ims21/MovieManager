from Components.MenuList import MenuList
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS
from enigma import eListboxPythonMultiContent, eListbox, gFont, getDesktop, RT_HALIGN_LEFT
from Tools.LoadPixmap import LoadPixmap
from .plugin import plugin_path
import skin


resolution = ""
if getDesktop(0).size().width() <= 1280:
	resolution = "_sd"
select_png = None
select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, plugin_path + "/png/select_on%s.png" % resolution))
if select_png is None:
	select_png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "icons/lock_on.png"))


def removeItemFromList(lst, item):
	for it in lst:
		if it[0][0:3] == item[0:3]:
			lst.remove(it)
			return

def MySelectionEntryComponent(description, value, index, selected):
	dx, dy, dw, dh = skin.parameters.get("ImsSelectionListDescr", (35, 2, 650, 30))
	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT, description)
	]
	if selected:
		ix, iy, iw, ih = skin.parameters.get("ImsSelectionListLock", (0, 0, 24, 24))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, select_png))
	return res


class MySelectionList(MenuList):
	def __init__(self, list=None, enableWrapAround=False):
		MenuList.__init__(self, list or [], enableWrapAround, content=eListboxPythonMultiContent)
		font = skin.fonts.get("ImsSelectionList", ("Regular", 20, 30))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])

	def addSelection(self, description, value, index, selected=True):
		self.list.append(MySelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		if len(self.list):
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
			self.setList(self.list)

	def getSelectionsList(self):
		return [(item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3]]

	def toggleAllSelection(self):
		for idx, item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def removeSelection(self, item):
		for it in self.list:
			if it[0][0:3] == item[0:3]:
				self.list.pop(self.list.index(it))
				self.setList(self.list)
				return

	def changeCurrentItem(self, item, new):
		if len(self.list):
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = MySelectionEntryComponent(new[0], new[1], new[2], new[3])
			self.setList(self.list)

	def toggleItemSelection(self, item):
		for idx, i in enumerate(self.list):
			if i[0][0:3] == item[0:3]:
				item = self.list[idx][0]
				self.list[idx] = MySelectionEntryComponent(item[0], item[1], item[2], not item[3])
				self.setList(self.list)
				return

	def sort(self, sortType=False, flag=False):
		# sorting by sortType: # 0 - name, 1 - item, 2 - index, 3 - selected
		if not sortType:
			if config.moviemanager.alphabetsort.value:
				from .dictsort import diacriticSorting
				self.list.sort(key=lambda x: (diacriticSorting(x[0][0]) and diacriticSorting(x[0][0]).lower()), reverse=flag)
			else:
				self.list.sort(key=lambda x: (x[0][0] and x[0][0].lower()), reverse=flag)
		else:
			self.list.sort(key=lambda x: x[0][sortType], reverse=flag)
		self.setList(self.list)

	def sortItemParts(self, sortType=False, flag=False):
		if sortType in (1,3):
			# sorting by sortType: # 0 - item, 1 - size, 2 - info, 3 - time
			self.list.sort(key=lambda x: x[0][1][sortType], reverse=flag)
		elif sortType == 10:
			from os import path
			# sorting by path, then alphabetical:
			self.list.sort(key=lambda x: (path.split(x[0][1][0].getPath())[0], x[0][0]), reverse=flag)
		self.setList(self.list)

	def len(self):
		return len(self.list)

	def markDuplicates(self, comma_index=0):
		seen = {}
		duplicates_keys = set()

		# find repeated keys
		for entry in self.list:
			description = entry[0][0].strip()
			parts = description.split(',')
			if comma_index != 3 and comma_index < len(parts):
				key = ','.join(parts[:comma_index + 1]).strip().lower()
			else:
				key = description.lower()
			if key in seen:
				duplicates_keys.add(key)
			else:
				seen[key] = entry

		# remark items with selected=True, it it is duplicete
		for idx, entry in enumerate(self.list):
			description, value, index, _ = entry[0]
			parts = description.split(',')
			if comma_index != 3 and comma_index < len(parts):
				key = ','.join(parts[:comma_index + 1]).strip().lower()
			else:
				key = description.lower()
			selected = key in duplicates_keys
			self.list[idx] = MySelectionEntryComponent(description, value, index, selected)

		self.setList(self.list)

	def keepOnlyDuplicates(self, comma_index=0):
		seen = {}
		duplicates_keys = set()

		# 1. find duplicates keys
		for entry in self.list:
			description = entry[0][0].strip()
			parts = description.split(',')
			if comma_index != 3 and comma_index < len(parts):
				key = ','.join(parts[:comma_index + 1]).strip().lower()
			else:
				key = description.lower()
			if key in seen:
				duplicates_keys.add(key)
			else:
				seen[key] = entry

		# 2. select diplicates only
		new_list = []
		for entry in self.list:
			description, value, index, _ = entry[0]
			parts = description.split(',')
			if comma_index != 3 and comma_index < len(parts):
				key = ','.join(parts[:comma_index + 1]).strip().lower()
			else:
				key = description.lower()
			if key in duplicates_keys:
				new_list.append(MySelectionEntryComponent(description, value, index, False)) # if you want marked duplicates, then replace 'False' with 'True'

		self.list = new_list
		self.setList(self.list)

	def resetList(self, items):
		self.list = []
		for description, value, index, selected in items:
			self.list.append(MySelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)