# -*-coding:utf-8 -*

import re

maj = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
minLetters = maj.lower()

def getBetween(str, sep) : 
	tmp = str.split(sep)
	return tmp[1]

def replaceBetween(add, str, sep, keepSep = True) : 
	"""Replace the substring in the string 'str' with the 'add' between the first 2 'sep'"""
	tmp = str.split(sep)
	if keepSep : 
		return tmp[0] + sep + add + sep + tmp[2]
	else : 
		return tmp[0] + add + tmp[2]

def addBetween(add, str, sep, keepSep = True) : 
	"""add to the substring in the string 'str' with the 'add' between the first 2 'sep'"""
	
	tmp = str.split(sep)
	if keepSep : 
		return tmp[0] + sep + tmp[1] + add + sep + tmp[2]
	else : 
		return tmp[0] + tmp[1] + add + tmp[2]

def replaceAllBetween(add, str, sep, keepSep = True) : 
	"""Replace the all the substring in the string 'str' with the 'add' between 2 'sep'"""

	#1, 3, 5, 7, 9

	tmp = str.split (sep)

	i = 1 
	while i< len(tmp) : 
		if keepSep : 
			tmp[i] = sep + add + sep
		else : 
			tmp[i] = add

		i +=2

	a = ""
	return a.join(tmp)


def convertVariableSynthax (var, isClass=True) : 
	if "_" in var : 
		n = var.replace ("_", " ")
		n = n.title() 
		n = n.replace (" ", "")

		if isClass==False : 
			n = n[0].lower() + n[1:]
		return n

	else : 
		tmp = re.findall('[A-Z][^A-Z]*', var)
		sep = "_"
		n = sep.join(tmp)
		n = n.lower()

		return n


def getCleanName(name, deleteSpace = True, deleteSpecialChar=True, deleteDotNComa=True) : 
	n = name.replace ("é", "e")
	n = n.replace ("è", "e")
	n = n.replace ("ê", "e")
	n = n.replace ("ë", "e")
	n = n.replace ("à", "a")
	n = n.replace ("@", "a")
	n = n.replace ("ï", "i")
	n = n.replace ("î", "i")
	n = n.replace ("ô", "o")
	n = n.replace ("ö", "o")
	n = n.replace ("ç", "c")
	n = n.replace ("ä", "a")
	n = n.replace ("â", "a")
	n = n.replace ("ü", "u")
	n = n.replace ("û", "u")
	n = n.replace ("ŷ", "y")
	n = n.replace ("ÿ", "y")
	n = n.replace ("ù", "u")

	if deleteSpace : 
		n = n.replace (" ", "_")

	if deleteSpecialChar : 
		n = n.replace ("$", "s")
		n = n.replace ("£", "l")
		n = n.replace ("¤", "")
		n = n.replace ("µ", "u")
		n = n.replace ("*", "")
		n = n.replace ("%", "")
		n = n.replace ("^", "")
		n = n.replace ("¨", "")
		n = n.replace ("&", "n")
		n = n.replace ("~", "")
		n = n.replace ("#", "")
		n = n.replace ("{", "")
		n = n.replace ("(", "")
		n = n.replace ("[", "")
		n = n.replace ("|", "")
		n = n.replace ("-", "")
		n = n.replace ("`", "")
		n = n.replace ("\\", "")
		n = n.replace (")", "")
		n = n.replace ("]", "")
		n = n.replace ("°", "")
		n = n.replace ("+", "")
		n = n.replace ("=", "")
		n = n.replace ("}", "")
		n = n.replace ("%", "")
		n = n.replace ("§", "")
		n = n.replace ("!", "")
		n = n.replace ("/", "")
		n = n.replace ("?", "")
	if deleteDotNComa : 
		n = n.replace ("<", "")
		n = n.replace (">", "")
		n = n.replace (".", "_")
		n = n.replace (";", "")
		n = n.replace (",", "")
		n = n.replace (":", "")

	return n


def readableNameFromVar(var) : 
	n = var.replace("_", " ")
	for i in range(len(n)) : 
		if n[i] in maj and i!=0 :
			if n[i-1] == " " : 
				continue
			n = n[:i] + " " + n[i:] 

	n = n.capitalize()
	return n

#if the string content is not a string like "True" or "2"
#it will return False
#useful for exec or eval statement
def isString(string) : 
    if string == "True" or string == "False" : 
        return False
    letters = "abcdefghijklmnopqrstuvwxy"

    for v in string : 
        if v.lower() in letters : 
            return True
    return False

def splitByIndexes(s, indexes) : 
    _idxs = []
    for i in indexes : 
        _idxs.append(i)
    _idxs.insert(0, 0)
    _idxs.append(len(s))
    return [s[_idxs[i]:_idxs[i + 1]] for i in range(len(_idxs) - 1)]

