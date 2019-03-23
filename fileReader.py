#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from emojiDbHandler import emojiDatabaseHandler
emojiDber = emojiDatabaseHandler()

jsonFile = "emojis\\emoji.json"

##Reads Emoji Json
def readEmojiJson(filePath):
	badLines = 0

	with open(filePath,encoding = "utf-8") as emojiFile:
		#must read the whole thing since each entry spread out over several lines
		lines = json.loads(emojiFile.read())

		for line in lines:
			try: emoji =  line["emoji"]
			except:
				badLines +=1
				continue

			category = line["category"].lower()

			#combine aliases and tags to get subcategories it belongs in
			subCategories = line["tags"] + line["aliases"]

			# use short description as name
			name = line["description"].lower()

			#print (("Name:%s \tCategory:%s \tEmoji:%s Subs:%s") % (name,category,emoji,subCategories))

			#add emoji
			emojiDber.addEmoji(emoji,name)

			#add english translation
			emojiDber.addEmojiTranslation(emoji,"English",name)

			#associate master category to itself
			emojiDber.associateMasterSubCategory("MASTER",category,emoji)

			#add subcategory assocatiations
			if subCategories:
				for subCategory in subCategories:
					emojiDber.associateMasterSubCategory(category,subCategory,emoji)
					emojiDber.addEmojiToSubcategory(subCategory,emoji)

			#associate emoji to main category also
			emojiDber.addEmojiToSubcategory(category,emoji)

		emojiFile.close()
		
		# print (badLines)

# readEmojiJson(jsonFile)




# #Reads a category file
# wordFile = "emojis\\wordsApi.json"
# with open(wordFile,encoding='utf8') as file:
# 	lines = json.loads(file.read())

# 	keys = list(lines.keys())

# 	pairsFound = 0

# 	for testKey in keys:
# 		# testKey = '60'
# 		# testKey = 'ablate'
# 		testEntry = lines[testKey]
# 		# print (testEntry)
# 		name = testKey
# 		categories = [name]

# 		if 'definitions' not in testEntry.keys():
# 			continue

# 		#check if the word has an emoji

# 		for definition in testEntry["definitions"]:
# 			defKeys = definition.keys()
# 			if 'typeOf' in defKeys: categories += definition['typeOf']
# 			if 'inCategory' in defKeys: categories += definition['inCategory']
# 			if 'synonyms' in defKeys: categories += definition['synonyms']
# 			if 'similarTo' in defKeys: categories += definition['similarTo']
		
# 		#check through every category found
# 		for category in categories:	
# 			#see if any match a named emoji
# 			namedEmojis = emojiDber.findEntryFromCollection("EMOJIS",
# 				{"NAME": category})

# 			#if they do, then add that emoji to every category found
# 			if namedEmojis:
# 				emoji = namedEmojis["EMOJI"]
# 				for relatedCategory in categories:
# 					if category != relatedCategory:
# 						emojiDber.addEmojiToSubcategory(SUBCATEGORY = relatedCategory,EMOJI = emoji)
# 						# pairsFound += 1

# 				# print (namedEmojis["EMOJI"],categories)

# 		# if not categories:
# 		# 	print (testKey,testEntry)
# 		# 	continue

# 		# print (name,categories)
# 	# print (pairsFound)
# 	file.close()





##Reads Emoji Text File
def getEmojiNamePair(lineIn):
	try:
		emojiNamePair =  (lineIn.rstrip("\n").split("(")[1]).split(")")
	except:
		print ("BAD LINE:", lineIn)
		return
		
	emoji = str(list(emojiNamePair[0])[0])

	name = emojiNamePair[1].lstrip(" ")

	isDoubleEmoji = (".." in emoji)

	output = name + "\t" + emoji + "\n"
	if isDoubleEmoji:
		emoji = emoji.split("..")
		name = name.split("..")
		output = name[0] + "\t" + emoji[0][0] + "\n" + name[1] + "\t" + emoji[1][0] + "\n"

	return output

def parseUnicodeFile(sourceFileName,sinkFileName):
	sourceFile = open(sourceFileName,"r", encoding="utf8")
	sinkFile = open(sinkFileName,"w",encoding = "utf8")

	for line in file.readlines():
		stringOut =  (getEmojiNamePair(line))
		sinkFile.write(stringOut)

	sourceFile.close()
	sinkFile.close()

# def loadCategoryDict(fileName):
# 	categoryDict = {}
# 	with open(fileName,"r",encoding = "utf-8") as categoryFile:
# 		for line in categoryFile.readlines():
# 			name,emoji = line.rstrip("\n").split("\t")
# 			categoryDict[name] = emoji

# 		categoryFile.close()
# 	return categoryDict