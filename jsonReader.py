import json

from emojiDbHandler import emojiDatabaseHandler
emojiDber = emojiDatabaseHandler()

def readEmojiJson(jsonFile):
	emojiFile = open(jsonFile,encoding = "utf-8")
	fileJson = json.loads(emojiFile.read())
	line = fileJson[0]
	print (line)

	# for line in fileJson:
		# try:
		# 	# print (line)
		# 	# print (line["category"],line["tags"],line["description"],line["emoji"])

	emoji =  ((line["emoji"][0]))
	category = line["category"]
	subCategories = line["tags"]
	name = line["description"]
	
	#add english translation
	emojiDber.addEmojiTranslation(emoji,name,"English")

	#add subcategory Assocatiations
	if subCategories:
		emojiDber.assignCategoryToEmoji(emoji,subCategories)
		emojiDber.addSubCategory(category,subCategories)
	else:
	#associate emoji to main category
		emojiDber.assignCategoryToEmoji(emoji,category)

		# 	print (("Name:%s \tCategory:%s \tEmoji:%s Subs:%s") % (name,category,emoji,subCategories))
		# except:
		# 	pass
			# print ("BAD LINE",line)
	# print (len(fileJson))
	emojiFile.close()

	# with open(jsonFile,encoding="utf-8") as emojiFile:
	# 	print (emojiFile.readline())
	# 	print (emojiFile.readline())
	# emojiFile.close()

jsonFile = "emoji.json"
readEmojiJson(jsonFile)