dictSortCZSK = {
#	u'ch': 'h|',
#	u'CH': 'H|',
#	u'Ch': 'H|',
#	u'cH': 'h|',
	u'\xc1': 'A|',
	u'\xc4': 'A}',
	u'\u010c': 'C|',
	u'\u010e': 'D|',
	u'\xc9': 'E|',
	u'\u011a': 'E}',
	u'\xcb': 'E~',
	u'\xcd': 'I|',
	u'\xcf': 'I}',
	u'\u0139': 'L|',
	u'\u013d': 'L}',
	u'\u0141': 'L~',
	u'\u0147': 'N|',
	u'\xd3': 'O|',
	u'\xd4': 'O}',
	u'\xd6': 'O~',
	u'\u0154': 'R|',
	u'\u0158': 'R}',
	u'\u0160': 'S|',
	u'\u0164': 'T|',
	u'\xda': 'U|',
	u'\u016e': 'U}',
	u'\xdc': 'U~',
	u'\xdd': 'Y|',
	u'\u0178': 'Y}',
	u'\u017d': 'Z|',
	u'\xe1': 'a|',
	u'\xe4': 'a}',
	u'\u010d': 'c|',
	u'\u010f': 'd|',
	u'\xe9': 'e|',
	u'\u011b': 'e}',
	u'\xeb': 'e~',
	u'\xed': 'i|',
	u'\xef': 'i}',
	u'\u013a': 'l|',
	u'\u013e': 'l}',
	u'\u0142': 'l~',
	u'\u0148': 'n|',
	u'\xf3': 'o|',
	u'\xf6': 'o}',
	u'\xf4': 'o~',
	u'\u0159': 'r|',
	u'\u0155': 'r}',
	u'\u0161': 's|',
	u'\u0165': 't|',
	u'\xfa': 'u|',
	u'\u016f': 'u}',
	u'\xfc': 'u~',
	u'\xfd': 'y|',
	u'\xff': 'y}',
	u'\u017e': 'z|'
}


def char2DiacriticSort(text):
	for c in unicode(text, "utf-8"):
		if ord(c) >= 0x80:
			converted = dictSortCZSK.get(c)
			if converted:
				text = text.replace(c, converted)
	text = text.replace('ch','h|').replace('Ch','H|').replace('CH','H|').replace('cH','h|')
	return text