# -*- coding: utf-8 -*-
# for localized messages
from . import _

#
#  Movie Manager - Plugin E2 for OpenPLi
VERSION = "1.78"
#  by ims (c) 2018 ims21@users.sourceforge.net
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

from Components.config import ConfigSubsection, config, ConfigYesNo, ConfigSelection, getConfigListEntry
from Screens.Screen import Screen
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.ActionMap import ActionMap, HelpableActionMap
from Screens.HelpMenu import HelpableScreen
from Components.ConfigList import ConfigListScreen
from enigma import eServiceReference, iServiceInformation, eServiceCenter, getDesktop, eSize, ePoint
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.Sources.ServiceEvent import ServiceEvent
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MovieSelection import buildMovieLocationList, copyServiceFiles, moveServiceFiles, last_selected_dest
from Screens.LocationBox import LocationBox, defaultInhibitDirs
from Components.MovieList import MovieList, StubInfo, IMAGE_EXTENSIONS, resetMoviePlayState, AUDIO_EXTENSIONS, MOVIE_EXTENSIONS, DVD_EXTENSIONS, moviePlayState
from Tools.BoundFunction import boundFunction
import os
import skin

MOVIE_EXTENSIONS1 = frozenset((".ts", ".mp4", ".mts", ".mkv", ".avi", ".mpg", ".webm"))
MOVIES_EXTENSIONS = MOVIE_EXTENSIONS.union(MOVIE_EXTENSIONS1)

def hex2strColor(argb):
	out = ""
	for i in range(28,-1,-4):
		out += "%s" % chr(0x30 + (argb>>i & 0xf))
	return out
try:
	fC = "\c%s" % hex2strColor(int(skin.parseColor("foreground").argb()))
except:
	fC = "\c%s" % hex2strColor(0x00f0f0f0)
gC = "\c%s" % hex2strColor(0x000ff80)

config.moviemanager = ConfigSubsection()
config.moviemanager.sensitive = ConfigYesNo(default=False)
config.moviemanager.search = ConfigSelection(default = "begin", choices = [("begin", _("start title")), ("end", _("end title")),("in", _("contains in title"))])
choicelist = []
for i in range(1, 11, 1):
	choicelist.append(("%d" % i))
choicelist.append(("15","15"))
choicelist.append(("20","20"))
config.moviemanager.length = ConfigSelection(default = "3", choices = [("0", _("No"))] + choicelist + [("255", _("All"))])
config.moviemanager.endlength = ConfigSelection(default = "5", choices = [("0", _("No"))] + choicelist + [("255", _("All"))])
config.moviemanager.add_bookmark = ConfigYesNo(default=False)
config.moviemanager.clear_bookmarks = ConfigYesNo(default=True)
config.moviemanager.manage_all = ConfigYesNo(default=False)
config.moviemanager.subdirs = ConfigYesNo(default=False)
config.moviemanager.movies = ConfigYesNo(default=True)
config.moviemanager.pictures = ConfigYesNo(default=False)
config.moviemanager.audios = ConfigYesNo(default=False)
config.moviemanager.dvds = ConfigYesNo(default=False)
config.moviemanager.sort = ConfigSelection(default = "0", choices = [
	("0", _("Original list")),
	("1", _("A-z sort")),
	("2", _("Z-a sort")),
	("3", _("Selected top")),
	("4", _("Original list - reverted"))
	])
config.moviemanager.position = ConfigYesNo(default=False)

cfg = config.moviemanager

LISTFILE = '/tmp/movies.csv'

def NAME(item):
	return item[0][0]
def ITEM(item):
	return item[0][1][0]
def SIZE(item):
	return item[0][1][1]
def LENGTH(item):
	return item[0][1][2]
def SELECTED(item):
	return item[0][3]

class MovieManager(Screen, HelpableScreen):
	skin="""
	<screen name="MovieManager" position="center,center" size="600,415" title="List of files">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="560,8" size="40,30" zPosition="2" alphatest="on"/>
		<widget name="config" position="5,50" zPosition="2" size="590,280" itemHeight="28" font="Regular;20" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,335" zPosition="2" size="590,2"/>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" foregroundColor="grey" font="Regular;18">
			<convert type="MovieInfo">RecordServiceName</convert>
		</widget>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" font="Regular;18" foregroundColor="grey"  halign="right">
			<convert type="MovieInfo">FileSize</convert>
		</widget>
		<widget source="Service" render="Label" position="5,342" size="590,28" transparent="1" font="Regular;18" foregroundColor="grey" halign="center">
			<convert type="ServiceTime">StartTime</convert>
			<convert type="ClockToText">Format:%a %d.%m.%Y, %H:%M</convert>
		</widget>
		<ePixmap pixmap="skin_default/div-h.png" position="5,363" zPosition="2" size="590,2"/>
		<widget name="number" position="5,372" size="135,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="size" position="5,392" size="135,20" zPosition="1" foregroundColor="green" font="Regular;16"/>
		<widget name="description" position="140,368" zPosition="2" size="470,46" valign="center" halign="left" font="Regular;16" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session, service=None, parent=None):
		Screen.__init__(self, session, parent = parent)
		HelpableScreen.__init__(self)
		self.session = session
		self.current = service
		self.parent = parent

		self.setTitle(_("List of files") + ":  %s" % config.movielist.last_videodir.value)
		self.original_selectionpng = None
		self.changePng()

		self["Service"] = ServiceEvent()

		self.accross = False
		self.position = -1
		self.size = 0
		self.list = SelectionList([])

		self["config"] = self.list
		self.getData(config.movielist.last_videodir.value)

		self["description"] = Label()

		self["size"] = Label()
		self["number"] = Label()

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Exit plugin")),
			"ok": (self.toggleSelection,_("Add or remove item of selection")),
			})
		### CSFDRunActions can be defined in keytranslation.xml
		self["CSFDRunActions"] = ActionMap(["CSFDRunActions"],
			{
				"csfd": self.csfd,
			})
		###
		textPreview = _("Preview")
		textForward = _("Skip forward") + " (" + textPreview +")"
		textBack = _("Skip backward") + " (" + textPreview +")"
		sfwd = lambda: self.seekRelative(1, config.seek.selfdefined_46.value * 90000)
		ssfwd = lambda: self.seekRelative(1, config.seek.selfdefined_79.value * 90000)
		sback = lambda: self.seekRelative(-1, config.seek.selfdefined_46.value * 90000)
		ssback = lambda: self.seekRelative(-1, config.seek.selfdefined_79.value * 90000)
		self["MovieManagerActions"] = HelpableActionMap(self, "MovieManagerActions",
			{
			"menu": (self.selectAction, _("Select action")),
			"red": (self.exit, _("Exit plugin")),
			"green": (self.selectAction, _("Select action")),
			"yellow": (self.sortIndex, _("Sort list")),
			"blue": (self.toggleAllSelection, _("Invert selection")),
			"preview": (self.playPreview, _("Preview")),
			"stop": (self.stopPreview, _("Stop")),
			"seekFwd": (sfwd, textForward),
			"seekFwdManual": (ssfwd, textForward),
			"seekBack": (sback, textBack),
			"seekBackManual": (ssback, textBack),
			"groupSelect": (boundFunction(self.selectGroup, True), _("Group selection - add")),
			"groupUnselect": (boundFunction(self.selectGroup, False), _("Group selection - remove")),
			"text": (self.saveList, _("Save list to '%s'") % "%s%s%s" % (gC,LISTFILE,fC)),
			"info": (self.displayInfo, _("Current item info")),
			}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Action"))
		self["key_yellow"] = Button(_("Sort"))
		self["key_blue"] = Button(_("Inversion"))

		self.playingRef = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self["description"].setText(_("Use 'Menu' or 'Action' for select operation. Multiple files mark with 'OK' or use 'CH+/CH-'."))

		self["config"].onSelectionChanged.append(self.setService)
		self.onShown.append(self.setService)
		self.onLayoutFinish.append(self.moveSelector)

	def parseMovieList(self, movielist, list):
		self.position = -1
		index = 0
		suma=0
		for i, record in enumerate(movielist):
			if record:
				item = record[0]
				if not item.flags & eServiceReference.mustDescent:
					ext = os.path.splitext(item.getPath())[1].lower()
					if not cfg.movies.value and ext in MOVIES_EXTENSIONS:
						continue
					if not cfg.pictures.value and ext in IMAGE_EXTENSIONS:
						continue
					if not cfg.audios.value and ext in AUDIO_EXTENSIONS:
						continue
					if not cfg.dvds.value and ext in DVD_EXTENSIONS:
						continue
					if self.current.getPath() == item.getPath():
						self.position = index
						print "[MovieManager] position found"
					info = record[1]
					name = info and info.getName(item)
					size = 0
					if info:
						if isinstance(info, StubInfo): # picture
							size = info.getInfo(item, iServiceInformation.sFileSize)
						else:
							size = info.getInfoObject(item, iServiceInformation.sFileSize) # movie
					list.list.append(SelectionEntryComponent(name, (item, size, info.getLength(item)), index, False))
					index += 1
					suma+=size
		self.l = SelectionList(list)
		self.l.setList(list)
		print "[MovieMnager} list filled with %s items. Size: %s, position %s" % (index, self.convertSize(suma), self.position)
		self.size = 0
		return list

	def moveSelector(self):
		self["config"].moveToIndex(self.position)
		self.setService()

	def seekRelative(self, direction, amount):
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekRelative(direction, amount)

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		seek = service.seek()
		if seek is None or not seek.isCurrentlySeekable():
			return None
		return seek

	def playPreview(self):
		item = self["config"].getCurrent()
		if item:
			path = ITEM(item).getPath()
			ext = os.path.splitext(path)[1].lower()
			if ext in IMAGE_EXTENSIONS:
				try:
					from Plugins.Extensions.PicturePlayer import ui
					self.session.open(ui.Pic_Full_View, [((path, False), None)], 0, path)
				except Exception, ex:
					print "[MovieManager] Cannot display", str(ex)
					return
			else:
				self.session.nav.playService(ITEM(item))

	def stopPreview(self):
		self.session.nav.playService(self.playingRef)

	def selectGroup(self, mark=True):
		def getSubstring(value):
			if value == "begin":
				return _("starts with...")
			elif value == "end":
				return _("ends with...")
			else:
				return _("contains...")
		if mark:
			txt = _("Add to selection (%s)") % getSubstring(cfg.search.value)
		else:
			txt = _("Remove from selection (%s)")  % getSubstring(cfg.search.value)
		item = self["config"].getCurrent()
		length = int(cfg.length.value)
		endlength = int(cfg.endlength.value)
		name = ""
		if item:
			if cfg.search.value == "begin" and length:
				name = NAME(item).decode('UTF-8', 'replace')[0:length]
				txt += 10*" " + "%s" % length
			elif cfg.search.value == "end" and endlength:
				name = NAME(item).decode('UTF-8', 'replace')[-endlength:]
				txt += 10*" " + "%s" % endlength
		self.session.openWithCallback(boundFunction(self.changeItems, mark), VirtualKeyBoard, title = txt, text = name)

	def changeItems(self, mark, searchString = None):
		if searchString:
			searchString = searchString.decode('UTF-8', 'replace')
			if not cfg.sensitive.value:
				searchString = searchString.lower()
			for item in self.list.list:
				if cfg.sensitive.value:
					if cfg.search.value == "begin":
						exist = NAME(item).decode('UTF-8', 'replace').startswith(searchString)
					elif cfg.search.value == "end":
						exist = NAME(item).decode('UTF-8', 'replace').endswith(searchString)
					else:
						exist = False if NAME(item).decode('UTF-8', 'replace').find(searchString)== -1 else True
				else:
					if cfg.search.value == "begin":
						exist = NAME(item).decode('UTF-8', 'replace').lower().startswith(searchString)
					elif cfg.search.value == "end":
						exist = NAME(item).decode('UTF-8', 'replace').lower().endswith(searchString)
					else:
						exist = False if NAME(item).decode('UTF-8', 'replace').lower().find(searchString)== -1 else True
				if exist:
					if mark:
						if not SELECTED(item):
							self.list.toggleItemSelection(item[0])
					else:
						if SELECTED(item):
							self.list.toggleItemSelection(item[0])
		self.displaySelectionPars()

	def selectAction(self):
		menu = []
		menu.append((_("Copy to..."),5))
		menu.append((_("Move to..."),6))
		keys = ["5","6"]
		menu.append((_("Rename"),2))
		keys += ["2"]
		if config.usage.setup_level.index == 2:
			menu.append((_("Delete"),8))
			keys += ["8"]
		if cfg.clear_bookmarks.value:
			menu.append((_("Clear bookmarks..."),10))
			keys += [""]
		menu.append((_("Reset playback position"),15))
		keys+=[""]
		menu.append((_("Create directory"),7))
		keys+=["7"]
		menu.append((_("Sort by..."),17))
		keys+=["yellow"]
		if cfg.manage_all.value:
			menu.append((_("Manage files in active bookmarks..."),18))
			keys += ["red"]
		menu.append((_("Options..."),20))
		keys += ["menu"]

		text = _("Select operation:")
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=text, list=menu, keys=keys)

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1] == 2:
			self.renameItem()
		if choice[1] == 5:
			self.copySelected()
		elif choice[1] == 6:
			self.moveSelected()
		elif choice[1] == 8:
			self.deleteSelected()
		elif choice[1] == 10:
			self.session.open(MovieManagerClearBookmarks)
		elif choice[1] == 15:
			self.resetSelected()
		elif choice[1] == 7:
			self.createDir()
		elif choice[1] == 17:
			self.selectSortby()
		elif choice[1] == 18:
			self.accross = cfg.manage_all.value
			self.getData()
		elif choice[1] == 20:
			def cfgCallBack(choice=False):
				cfg_after = self.getCfgStatus()
				if self.cfg_before != cfg_after:
					if (cfg_after & 0x20) - (self.cfg_before & 0x20) < 0: # all -> single
						self.accross = cfg.manage_all.value
					path = config.movielist.last_videodir.value
					if self.accross:
						path = None
					self.getData(path)
			self.cfg_before = self.getCfgStatus()
			self.session.openWithCallback(cfgCallBack, MovieManagerCfg)

	def createDir(self):
		self.session.openWithCallback(self.parent.createDirCallback, VirtualKeyBoard,
			title = _("New directory name in '%s'") % config.movielist.last_videodir.value, text = "")

	def getCfgStatus(self):
		s =  0x01 if cfg.subdirs.value else 0
		s += 0x02 if cfg.movies.value else 0
		s += 0x04 if cfg.audios.value else 0
		s += 0x08 if cfg.pictures.value else 0
		s += 0x10 if cfg.dvds.value else 0
		s += 0x20 if cfg.manage_all.value else 0
		return s

	def saveList(self):
		import codecs
		fo = open("%s" % LISTFILE, "w")
		fo.write(codecs.BOM_UTF8)
		fo.write("%s;%s;%s\n" % (_("name"),_("size"),_("path")))
		for item in self.list.list:
			name = NAME(item)
			size = self.convertSize(SIZE(item))
			path = os.path.split(ITEM(item).getPath())[0]
			line = "%s;%s;%s\n" % (name, size, path)
			fo.write(line)
		fo.close()

	def selectSortby(self):
		menu = []
		for x in cfg.sort.choices.choices:
			menu.append((x[1], x[0]))
		self.session.openWithCallback(self.sortbyCallback, ChoiceBox, title=_("Sort list:"), list=menu, selection=int(cfg.sort.value))

	def sortbyCallback(self, choice):
		if choice is None:
			return
		self.sortList(int(choice[1]))

	def renameItem(self):
		if not len(self["config"].list):
			return
		# item ... (name, (service, size), index, status)
		self.extension = ""
		item = self["config"].getCurrent()
		if item:
			name = NAME(item)
			full_name = os.path.split(ITEM(item).getPath())
			if full_name == name: # split extensions for files without metafile
				name, self.extension = os.path.splitext(name)
		self.session.openWithCallback(self.renameCallback, VirtualKeyBoard, title = _("Rename"), text = name)

	def renameCallback(self, name):
		def renameItemInList(list, item, newname):
			a = []
			for list_item in list.list:
				if list_item[0] == item[0]:
					list_item[0] = (newname,) + list_item[0][1:]
					self.position = list_item[0][2]
				a.append(list_item)
			return a
		def reloadNewList(newlist, list):
			index = 0
			for n in newlist:
				item = n[0]
				list.list.append(SelectionEntryComponent(item[0], item[1], index, item[3]))
				index+=1
			self.l = SelectionList(list)
			self.l.setList(list)
			return list
		def renameItem(item, newname, list):
			new = renameItemInList(list, item, newname)
			self.clearList()
			return reloadNewList(new, self.list)

		if not name:
			return
		msg = None
		name = "".join((name.strip(), self.extension))
		item = self["config"].getCurrent()
		if item and ITEM(item):
			try:
				path = ITEM(item).getPath().rstrip('/')
				meta = path + '.meta'
				if os.path.isfile(meta):
					metafile = open(meta, "r+")
					sid = metafile.readline()
					oldtitle = metafile.readline()
					rest = metafile.read()
					metafile.seek(0)
					metafile.write("%s%s\n%s" %(sid, name, rest))
					metafile.truncate()
					metafile.close()
				else:
					pathname,filename = os.path.split(path)
					newpath = os.path.join(pathname, name)
					print "[MovieManager] rename", path, "to", newpath
					os.rename(path, newpath)
				idx = self.getItemIndex(item)
				self.list = renameItem(item, name, self.list)
				self["config"].moveToIndex(idx)
			except OSError, e:
				print "Error %s:" % e.errno, e
				if e.errno == 17:
					msg = _("The path %s already exists.") % name
				else:
					msg = _("Error") + '\n' + str(e)
			except Exception, e:
				import traceback
				print "[MovieManager] Unexpected error:", e
				traceback.print_exc()
				msg = _("Error") + '\n' + str(e)
			if msg:
				self.session.open(MessageBox, msg, type = MessageBox.TYPE_ERROR, timeout = 5)

	def getData(self, current_dir=None):
		def lookDirs(path):
			paths = []
			for path, dirs, files in os.walk(path):
				if path.find("BDMV") == -1 and path.find("VIDEO_TS") == -1 and path.find("AUDIO_TS") == -1: # and path.find(".Trash") == -1:
					if not path.endswith('/'):
						path += '/'
					paths.append(path)
			return paths
		def setCurrentRef(path):
			self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + path)
			if cfg.pictures.value:
				self.current_ref.setName('16384:jpg 16384:png 16384:gif 16384:bmp 16384:jpeg')
		def readDirectory(path):
			setCurrentRef(path)
			list = MovieList(None, sort_type=MovieList.SORT_GROUPWISE)
			list.reload(self.current_ref, [])
			return list
		def readSubdirs(path):
			files = []
			for subdir in lookDirs(path):
				files += readDirectory(subdir)
				print "[MovieManager] + added files from %s" % subdir
			return files
		def readLists(current_dir=None):
			files = []
			if config.movielist.videodirs.saved_value and not current_dir:
				for path in eval(config.movielist.videodirs.saved_value):
					if cfg.subdirs.value:
						files += readSubdirs(path)
					else:
						files += readDirectory(path)
					print "[MovieManager] + added files from %s" % path
				print "[MovieManager] readed items from directories in bookmarks."
			elif current_dir:
				if cfg.subdirs.value:
					files = readSubdirs(current_dir)
				else:
					files += readDirectory(current_dir)
				print "[MovieManager] + added files from %s" % current_dir
			else:
				print "[MovieManager] no valid bookmarks!"
			return files

		if len(self["config"].list):
			item = self["config"].getCurrent()
			self.current = ITEM(item)
		self.clearList()
		self.list = self.parseMovieList(readLists(current_dir), self.list)
		self.sortList(int(cfg.sort.value))
		if cfg.position.value:
			if self.position >= 0:
				self.position = self.newPositionIndex(self.position)
		else:
			self.position = -1
		self["config"].moveToIndex(self.position)

	def toggleAllSelection(self):
		self.list.toggleAllSelection()
		self.displaySelectionPars()

	def toggleSelection(self):
		self.list.toggleSelection()
		item = self["config"].getCurrent()
		if item:
			size = SIZE(item)
			selected = SELECTED(item)
			self.size = self.size + size if selected else self.size - size
		self.displaySelectionPars(True)

	def displaySelectionPars(self, singleToggle=False):
		size = ""
		number = ""
		selected = len(self.list.getSelectionsList())
		if selected:
			if singleToggle:
				size = self.convertSize(self.size)
			else:
				size = self.countSizeSelectedItems()
			size = _("Size: %s") % size
			number = _("Selected: %s") % selected
		self["number"].setText(number)
		self["size"].setText(size)

	def countSizeSelectedItems(self):
		self.size = 0
		data = self.list.getSelectionsList()
		if len(data):
			for item in data:
				self.size += item[1][1]
			return "%s" % self.convertSize(self.size)
		return ""

	def setService(self):
		item = self["config"].getCurrent()
		if item:
			self["Service"].newService(ITEM(item))
			if self.accross or cfg.subdirs.value:
				self.setTitle(_("List of files") + ":  %s" % os.path.realpath(ITEM(item).getPath()).rpartition('/')[0])
		else:
			self["Service"].newService(None)

	def displayInfo(self):
		item = self["config"].getCurrent()
		if item:
			self.session.open(MovieManagerFileInfo, (item, self.getLastPlayedPosition(item), self.convertSize(SIZE(item))))

	def getLastPlayedPosition(self, item):
		lastposition = moviePlayState(ITEM(item).getPath()+'.cuts' ,ITEM(item), LENGTH(item))
		if lastposition:
			return "%s%s" % (lastposition, '%')
		return ""

	def changePng(self):
		path = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/mark_select.png")
		if os.path.exists(path):
			import Components.SelectionList
			self.original_selectionpng = Components.SelectionList.selectionpng
			Components.SelectionList.selectionpng = LoadPixmap(cached=True, path=path)

	def getItemIndex(self, item):
		index = 0
		for i in self["config"].list:
			if i[0] == item[0]:
				return index
			index += 1
		return 0

	def newPositionIndex(self, old_position):
		index = 0
		for i in self["config"].list:
			if i[0][2] == old_position:
					return index
			index += 1
		return 0

	def clearList(self):
		self.l = self.list
		self.l.setList([])

	def sortIndex(self):
		sort = int(config.moviemanager.sort.value)
		sort +=1
		if sort == 3 and  not len(self.list.getSelectionsList()):
			sort +=1
		sort %=5
		self.sortList(sort)

	def sortList(self, sort):
		if len(self["config"].list):
			item = self["config"].getCurrent()
			if sort == 0:	# original input list
				self.list.sort(sortType=2)
			elif sort == 1:	# a-z
				self.list.sort(sortType=0)
			elif sort == 2:	# z-a
				self.list.sort(sortType=0, flag=True)
			elif sort == 3:	# selected top
				self.list.sort(sortType=3, flag=True)
			elif sort == 4:	# original input list reverted
				self.list.sort(sortType=2, flag=True)
			idx = self.getItemIndex(item)
			self["config"].moveToIndex(idx)
			config.moviemanager.sort.value = str(sort)

	def deleteSelected(self):
		def firstConfirmForDelete(choice):
			if choice:
				self.session.openWithCallback(self.delete, MessageBox, _("Plugin does not use the trash or check a running recording!\nDo You want continue and delete %s selected files?") % selected, type=MessageBox.TYPE_YESNO, default=False)
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(firstConfirmForDelete, MessageBox, _("Are You sure to delete %s selected file(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def delete(self, choice):
		if choice:
			data = self.list.getSelectionsList()
			selected = len(data)
			if not selected:
				data = [self["config"].getCurrent()[0]]
				self.size = SIZE(data)
				selected = 1
			deleted = 0
			for item in data:
				# item ... (name, (service, size), index, status)
				if self.deleteConfirmed(item):
					deleted += 1
			self.displaySelectionPars()
			self.session.open(MessageBox, _("Sucessfuly deleted %s of %s files...") % (selected, deleted), type=MessageBox.TYPE_INFO, timeout=5)
			if not len(self.list.list):
				self.exit()

	def deleteConfirmed(self, item):
		name = item[0]
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(item[1][0])
		try:
			if offline is None:
			        from enigma import eBackgroundFileEraser
			        eBackgroundFileEraser.getInstance().erase(os.path.realpath(item[1][0].getPath()))
			else:
				if offline.deleteFromDisk(0):
					raise Exception, "Offline delete failed"
			self.list.removeSelection(item)
			from Screens.InfoBarGenerics import delResumePoint
			delResumePoint(item[1][0])
			return True
		except Exception, ex:
			self.session.open(MessageBox, _("Delete failed!") + "\n" + name + "\n" + str(ex), MessageBox.TYPE_ERROR, timeout=3)
			return False

	def copySelected(self):
		if self["config"].getCurrent():
			self.selectMovieLocation(title=_("Select destination for copy selected files..."), callback=self.gotCopyMovieDest)

	def gotCopyMovieDest(self, choice):
		if not choice:
			return
		dest = os.path.normpath(choice)
		if dest == config.movielist.last_videodir.value[0:-1]:
			self.session.open(MessageBox, _("Same source and target directory!"), MessageBox.TYPE_ERROR, timeout=3)
			return

		toggle = True
		data = self.list.getSelectionsList()
		if len(data) == 0:
			data = [self["config"].getCurrent()[0]]
			self.size = SIZE(data)
			toggle = False
		if not self.isFreeSpace(dest):
			return
		if len(data):
			for item in data:
				try:
					# item ... (name, (service, size, length), index, status)
					copyServiceFiles(item[1][0], dest, item[0])
					if toggle:
						self.list.toggleItemSelection(item)
				except Exception, e:
					self.session.open(MessageBox, str(e), MessageBox.TYPE_ERROR, timeout=2)
		self.displaySelectionPars()

	def moveSelected(self):
		if self["config"].getCurrent():
			self.selectMovieLocation(title=_("Select destination for move selected files..."), callback=self.gotMoveMovieDest)

	def gotMoveMovieDest(self, choice):
		if not choice:
			return
		dest = os.path.normpath(choice)
		src = config.movielist.last_videodir.value
		if dest == src[0:-1]:
			self.session.open(MessageBox, _("Same source and target directory!"), MessageBox.TYPE_ERROR, timeout=3)
			return
		data = self.list.getSelectionsList()
		if len(data) == 0:
			data = [self["config"].getCurrent()[0]]
			self.size = SIZE(data)
		if not self.isSameDevice(src, dest):
			if not self.isFreeSpace(dest):
				return
		if len(data):
			for item in data:
				try:
					# item ... (name, (service, size, length), index, status)
					moveServiceFiles(item[1][0], dest, item[0])
					self.list.removeSelection(item)
				except Exception, e:
					self.session.open(MessageBox, str(e), MessageBox.TYPE_ERROR, timeout=3 )
		self.displaySelectionPars()
		if not len(self.list.list):
			self.exit()

	def isSameDevice(self, src, dest):
		if os.stat(src).st_dev != os.stat(dest).st_dev:
			return False
		return True

	def freeSpace(self, path):
		dev = os.statvfs(path)
		return dev.f_bfree * dev.f_bsize

	def isFreeSpace(self, dest):
		free_space = self.freeSpace(dest)
		if free_space <= self.size:
			self.session.open(MessageBox, _("On destination '%s' is %s free space only!") % (dest, self.convertSize(free_space)), MessageBox.TYPE_ERROR, timeout=5)
			return False
		return True

	def resetSelected(self):
		if self["config"].getCurrent():
			toggle = True
			data = self.list.getSelectionsList()
			if len(data) == 0:
				data = [self["config"].getCurrent()[0]]
				toggle = False
			if len(data):
				for item in data:
					# 0 - name, 1 - (0 - item, 1-size, 2-length), 2-index
					current = item[1][0]
					resetMoviePlayState(current.getPath() + ".cuts", current)
					if toggle:
						self.list.toggleItemSelection(item)
			self.displaySelectionPars()

	def exit(self):
		config.moviemanager.sort.save()
		if self.original_selectionpng:
			import Components.SelectionList
			Components.SelectionList.selectionpng = self.original_selectionpng
		self.session.nav.playService(self.playingRef)
		self.close()
		self.parent.reloadList()

	def selectMovieLocation(self, title, callback):
		bookmarks = [("("+_("Other")+"...)", None)]
		buildMovieLocationList(bookmarks)
		self.onMovieSelected = callback
		self.movieSelectTitle = title
		self.session.openWithCallback(self.gotMovieLocation, ChoiceBox, title=title, list=bookmarks)

	def gotMovieLocation(self, choice):
		if not choice:
			# cancelled
			self.onMovieSelected(None)
			del self.onMovieSelected
			return
		if isinstance(choice, tuple):
			if choice[1] is None:
				# Display full browser, which returns string
				self.session.openWithCallback(self.gotMovieLocation, MyMovieLocationBox, self.movieSelectTitle, config.movielist.last_videodir.value)
				return
			choice = choice[1]
		choice = os.path.normpath(choice)

		self.rememberMovieLocation(choice)
		self.onMovieSelected(choice)
		del self.onMovieSelected

	def rememberMovieLocation(self, where):
		if where in last_selected_dest:
			last_selected_dest.remove(where)
		last_selected_dest.insert(0, where)
		if len(last_selected_dest) > 5:
			del last_selected_dest[-1]

	def convertSize(self, filesize):
		if filesize:
			if filesize >= 104857600000:
				return _("%.0f GB") % (filesize / 1073741824.0)
			elif filesize >= 1073741824:
				return _("%.2f GB") % (filesize / 1073741824.0)
			elif filesize >= 1048576:
				return _("%.0f MB") % (filesize / 1048576.0)
			elif filesize >= 1024:
				return _("%.0f kB") % (filesize / 1024.0)
			return _("%d B") % filesize
		return ""

	def csfd(self):
		def isCSFD():
			try:
				from Plugins.Extensions.CSFD.plugin import CSFD
			except ImportError:
				self.session.open(MessageBox, _("The CSFD plugin is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 5 )
				return False
			else:
				return True
		if isCSFD():
			event = self["config"].getCurrent()
			if event:
				from Plugins.Extensions.CSFD.plugin import CSFD
				self.session.open(CSFD, event[0][0])

def MyMovieLocationBox(session, text, dir, filename = "", minFree = None):
	config.movielist.videodirs.load()
	return LocationBox(session, text = text,  filename = filename, currDir = dir, bookmarks = config.movielist.videodirs, autoAdd = cfg.add_bookmark.value, editDir = True, inhibitDirs = defaultInhibitDirs, minFree = minFree)

class MovieManagerCfg(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["MovieManagerCfg", "Setup"]
		self.setup_title = _("Options...") + "\t" + _("v.%s") % VERSION
		self.setTitle(self.setup_title)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))
		self["description"] = Label("")

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.save,
			"ok": self.save,
			"red": self.exit,
			"cancel": self.exit
		}, -2)
		self.list = []
		self.onChangedEntry = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
		self.loadMenu()

	def loadMenu(self):
		self.list = []
		self.search = _("Search in group selection by")
		self.list.append(getConfigListEntry(self.search, cfg.search, _("You can set what will group selection use - start of title, end of title or contains in title.")))
		if cfg.search.value == "begin":
			self.list.append(getConfigListEntry(_("Pre-fill first 'n' filename chars to virtual keyboard"), cfg.length, _("You can set the number of letters from the beginning of the current file name as the text pre-filled into virtual keyboard for easier input via group selection. For 'group selection' use 'CH+/CH-' buttons.")))
		elif cfg.search.value == "end":
			self.list.append(getConfigListEntry(_("Pre-fill last 'n' filename chars to virtual keyboard"), cfg.endlength, _("You can set the number of letters from the end of the current file name as the text pre-filled into virtual keyboard for easier input via group selection. For 'group selection' use 'CH+/CH-' buttons.")))
		self.list.append(getConfigListEntry(_("Compare case sensitive"), cfg.sensitive, _("Sets whether to distinguish between uper case and lower case for searching.")))
		self.list.append(getConfigListEntry(_("Use target directory as bookmark"), cfg.add_bookmark, _("Set 'yes' if You want add target directories into bookmarks.")))
		self.list.append(getConfigListEntry(_("Enable 'Clear bookmark...'"), cfg.clear_bookmarks, _("Enable in menu utility for delete bookmarks in menu.")))
		self.list.append(getConfigListEntry(_("Enable 'Manage files in active bookmarks...'"), cfg.manage_all, _("Enable in menu item for manage movies in all active bookmarks as one list.")))
		self.list.append(getConfigListEntry(_("Including subdirectories"), cfg.subdirs, _("If enabled, then will be used subdirectories too (it will take longer).")))
		self.list.append(getConfigListEntry(_("Movie files"), cfg.movies, _("If enabled, then will be added movie files into list.")))
		self.list.append(getConfigListEntry(_("Audio files"), cfg.audios, _("If enabled, then will be added audio files into list.")))
		self.list.append(getConfigListEntry(_("DVD images"), cfg.dvds, _("If enabled, then will be added dvd image files into list.")))
		self.list.append(getConfigListEntry(_("Pictures"), cfg.pictures, _("If enabled, then will be added pictures into list.")))
		self.list.append(getConfigListEntry(_("To maintain selector position"), cfg.position, _("If enabled, then will be on start maintained selector position in items list.")))
		self["config"].list = self.list

	# Summary - for (LCD):
	def changedEntry(self):
		if self["config"].getCurrent()[0] == self.search:
			self.loadMenu()
		for x in self.onChangedEntry:
			x()
	def getCurrentEntry(self):
		self["description"].setText(self["config"].getCurrent()[2])
		return self["config"].getCurrent()[0]
	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())
	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary
	###

	def save(self):
		self.keySave()

	def exit(self):
		self.keyCancel()

class MovieManagerClearBookmarks(Screen, HelpableScreen):
	skin="""
	<screen name="MovieManager" position="center,center" size="600,390" title="List of bookmarks">
		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap name="yellow" position="280,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap name="blue"   position="420,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="280,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="key_blue" position="420,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2"/>
		<widget name="config" position="5,50" zPosition="2" size="590,300" foregroundColor="white" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/div-h.png" position="5,355" zPosition="2" size="590,2"/>
		<widget name="description" position="5,360" zPosition="2" size="590,25" valign="center" halign="left" font="Regular;22" foregroundColor="white"/>
	</screen>
	"""
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["MovieManagerCfg", "Setup"]
		self.session = session

		self.setTitle(_("List of bookmarks"))

		self.list = SelectionList([])
		if self.loadAllMovielistVideodirs():
			index = 0
			for bookmark in eval(config.movielist.videodirs.saved_value):
				self.list.addSelection(bookmark, bookmark, index, False)
				index += 1
		self["config"] = self.list

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.exit, _("Close")),
			"ok": (self.list.toggleSelection, _("Add or remove item of selection")),
			})
		self["MovieManagerActions"] = HelpableActionMap(self, "MovieManagerActions",
			{
			"red": (self.exit, _("Close")),
			"green": (self.deleteSelected, _("Delete selected")),
			"yellow": (self.sortList, _("Sort list")),
			"blue": (self.list.toggleAllSelection, _("Invert selection")),
			}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Delete"))
		self["key_yellow"] = Button(_("Sort"))
		self["key_blue"] = Button(_("Inversion"))

		self.sort = 0
		self["description"] = Label(_("Select with 'OK' and then remove with 'Delete'."))
		self["config"].onSelectionChanged.append(self.bookmark)

	def loadAllMovielistVideodirs(self):
		if config.movielist.videodirs.saved_value:
			sv = config.movielist.videodirs.saved_value
			tmp = eval(sv)
			locations = [[x, None, False, False] for x in tmp]
			for x in locations:
				x[1] = x[0]
				x[2] = True
			config.movielist.videodirs.locations = locations
			return True
		return False

	def bookmark(self):
		if len(self["config"].list):
			item = self["config"].getCurrent()
			if item:
				text = "%s" % NAME(item)
				self["description"].setText(text)
		else:
			self["description"].setText("")

	def sortList(self):
		if self.sort == 0:	# z-a
			self.list.sort(sortType=0, flag=True)
			self.sort = 1
		elif self.sort == 1:
			if len(self.list.getSelectionsList()):	# selected top
				self.list.sort(sortType=3, flag=True)
				self.sort = 2
			else:		# a-z
				self.list.sort(sortType=0)
				self.sort = 0
		elif self.sort == 2:	# a-z
			self.list.sort(sortType=0)
			self.sort = 0

	def deleteSelected(self):
		if self["config"].getCurrent():
			selected = len(self.list.getSelectionsList())
			if not selected:
				selected = 1
			self.session.openWithCallback(self.delete, MessageBox, _("Are You sure to delete %s selected bookmark(s)?") % selected, type=MessageBox.TYPE_YESNO, default=False)

	def delete(self, choice):
		if choice:
			bookmarks = config.movielist.videodirs.value
			data = self.list.getSelectionsList()
			selected = len(data)
			if not selected:
				data = [self["config"].getCurrent()[0]]
				selected = 1
			for item in data:
				# item ... (name, name, index, status)
				self.list.removeSelection(item)
				bookmarks.remove(item[0])
			config.movielist.videodirs.value = bookmarks
			config.movielist.videodirs.save()

	def exit(self):
		self.close()

class MovieManagerFileInfo(Screen):
	skin="""
	<screen name="MovieManagerFileInfo" position="fill" title="Info" flags="wfNoBorder" backgroundColor="background">
		<widget name="name" render="Label" position="10,15" size="1920,30" font="Regular;26"/>
		<widget name="path" render="Label" position="10,45" size="1920,30" font="Regular;26" foregroundColor="green"/>
		<widget source="service" render="Label" position="10,75" size="290,30" font="Regular;26" foregroundColor="grey">
			<convert type="ServiceTime">StartTime</convert>
			<convert type="ClockToText">Format:%a %d.%m.%Y, %H:%M</convert>
		</widget>
		<widget source="service" render="Label" position="300,75" size="600,30" font="Regular;26" foregroundColor="grey">
			<convert type="MovieInfo">RecordServiceName</convert>
		</widget>
		<widget name="size" render="Label" position="10,105" size="100,30" font="Regular;26" foregroundColor="blue"/>
		<widget name="play" render="Label" position="150,105" size="100,30" font="Regular;26" foregroundColor="yellow"/>
	</screen>"""

	def __init__(self, session, (item, last, size)):
		Screen.__init__(self, session)
		self.session = session

		self.path = ITEM(item).getPath()
		self["name"] = Label("%s" % NAME(item))
		self["path"] = Label()
		self["size"] = Label("%s" % size)
		self["play"] = Label("%s" % last)
		self["service"] = ServiceEvent()
		self["service"].newService(ITEM(item))

		self["actions"] = ActionMap(["MovieManagerActions", "OkCancelActions"],
		{
			"ok": self.exit,
			"cancel": self.exit,
			"green": self.exit,
			"red": self.exit,
			"info": self.exit,
		}, -2)
		self.onLayoutFinish.append(self.setSize)

	def setSize(self):
		x,y = self.getLineSize()
		wsize = (x + 2*10, 5*y)
		self.instance.resize(eSize(*wsize))
		w,h = self.getScreenSize()
		wx = (w - wsize[0])/2
		wy = (h - wsize[1])/2
		self.instance.move(ePoint(wx,wy))

	def getLineSize(self):
		self["path"].instance.setNoWrap(1)
		self["path"].setText("%s" % self.path)
		return self["path"].instance.calculateSize().width(), self["path"].instance.calculateSize().height()

	def getScreenSize(self):
		desktop = getDesktop(0)
		return desktop.size().width(), desktop.size().height()

	def exit(self):
		self.close()
