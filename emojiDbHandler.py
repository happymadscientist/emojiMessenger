from pymongo import MongoClient
import pymongo

from datetime import datetime

class emojiDatabaseHandler:

	def __init__(self):
		self.loadEmojiDatabase()

	def loadEmojiDatabase(self):
		mongoClient = MongoClient('mongodb://localhost:27017/')
		self.emojiDb = mongoClient["emojiDb"]

	def createTables(self):
		self.emojiDb["EMOJI_TRANSLATIONS"].create_index([('EMOJI', pymongo.TEXT)],unique = True)
		self.emojiDb["CATEGORIES"].create_index({'MASTER':1,'SUB':1},unique = True)
		self.emojiDb["ENTERED_STRINGS"].create_index([('TIMESTAMP', pymongo.ASCENDING)],unique = True)
		self.emojiDb["EMOJI_SUBCATEGORIES"].create_index([('EMOJI', pymongo.TEXT),('CATEGORY', pymongo.TEXT)])
		self.emojiDb["CATEGORY_ICONS"].create_index([('EMOJI', pymongo.TEXT),('CATEGORY', pymongo.TEXT)])

	def dropCollection(self,COLLECTION_NAME):
		self.emojiDb.drop_collection(COLLECTION_NAME)

	def dropAllCollections(self):
		self.dropCollection("EMOJI_TRANSLATIONS")
		self.dropCollection("CATEGORIES")
		self.dropCollection("ENTERED_STRINGS")
		self.dropCollection("EMOJI_SUBCATEGORIES")
		self.dropCollection("CATEGORY_ICONS")
		self.createTables()

	def addEntryToCollection(self,COLLECTION_NAME,ENTRY):
		print (ENTRY)
		try:
			return self.emojiDb[COLLECTION_NAME].insert_one(ENTRY)
		except:
			print ("FAILED")

	def updateColumnOfEntry(self,COLLECTION_NAME,ENTRY,UPDATE):
		return self.emojiDb[COLLECTION_NAME].update_one(ENTRY, {"$set": UPDATE}, upsert=True)

	def updateListOfEntry(self,COLLECTION_NAME,ENTRY,UPDATE):
		self.emojiDb[COLLECTION_NAME].update_one(ENTRY, {'$push': UPDATE})

	def findOneEntry(self,COLLECTION_NAME,ENTRY_CRITERIA,MASK_CRITERIA={"_id":0}):
		return self.emojiDb[COLLECTION_NAME].find_one(ENTRY_CRITERIA,MASK_CRITERIA)
	
	def findManyEntries(self,COLLECTION_NAME,ENTRY_CRITERIA,MASK_CRITERIA={"_id":0}):
		return self.emojiDb[COLLECTION_NAME].find(ENTRY_CRITERIA,MASK_CRITERIA)

	def cursorToList(self,cursorIn):
		return list(cursorIn)

	def printAllEntries(self,COLLECTION_NAME):
		for entry in self.emojiDb[COLLECTION_NAME].find({},{"_id":0}):
			print (entry)

	#EMOJI TRANSLATION TABLE METHODS
	# def addEmoji(self,emoji):
	# 	self.addEntryToCollection("EMOJI_TRANSLATIONS",{"EMOJI":emoji})

	def addEmojiTranslation(self,emoji,translation,language):
		self.updateColumnOfEntry("EMOJI_TRANSLATIONS",{"EMOJI":emoji},{language:translation})
	
	def getEmojiTranslations(self,emoji):
		return self.findOneEntry("EMOJI_TRANSLATIONS",
			{"EMOJI":emoji},
			{"_id":0,"EMOJI":0}
			)

	#CATEGORY_ICONS
	def assignIconToCategory(self,emoji,category):
		self.addEntryToCollection("CATEGORY_ICONS",{"EMOJI":emoji,"CATEGORY":category})

	def getCategoryIcon(self,category):
		return self.findOneEntry("CATEGORY_ICONS",
			{"CATEGORY":category},
			{"_id":0,"EMOJI":1}
			)["EMOJI"]

	# def getCategoryIcons(self,category)
	#EMOJI_SUBCATEGORIES
	
	def assignCategoryToEmoji(self,emoji,category):
		if type(category) is list:
			for cat in category:	
				self.addEntryToCollection("EMOJI_SUBCATEGORIES",{"EMOJI":emoji,"CATEGORY":cat})
		else:
			self.addEntryToCollection("EMOJI_SUBCATEGORIES",{"EMOJI":emoji,"CATEGORY":category})

	def getEmojisOfCategory(self,category):
		emojiCategoryCursor =  self.findManyEntries("EMOJI_SUBCATEGORIES",
			{"CATEGORY":category},
			{"_id":0,"EMOJI":1}
			).distinct("EMOJI")

		return self.cursorToList(emojiCategoryCursor)

	#CATEGORIES
	# def addMasterCategory(self,categoryName):
	# 	self.addEntryToCollection("CATEGORIES",{"MASTER":categoryName,"SUB":[]})

	def addSubCategory(self,masterCategoryName,subCategoryName):
		if type(subCategoryName) is list:
			for subCategory in subCategoryName:
				# try:
				self.addEntryToCollection("CATEGORIES",{"MASTER":masterCategoryName,"SUB":subCategory})
				# except:
					# print ("Failed to add category: Master:",masterCategoryName,"Sub:",subCategory)
		else:
			self.addEntryToCollection("CATEGORIES",{"MASTER":masterCategoryName,"SUB":subCategoryName})

	def getSubCategories(self,masterCategoryName):
		return self.cursorToList(self.findManyEntries("CATEGORIES",{"MASTER":masterCategoryName},{"_id":0,"SUB":1}).distinct("SUB"))

	def getMasterCategoriesDict(self):
		emojiCategoryCursor =  self.findManyEntries("CATEGORIES",
			{"CATEGORY":category},
			{"_id":0,"EMOJI":1}
			).distinct("EMOJI")

		return self.cursorToList(emojiCategoryCursor)

	#ENTERED STRINGS
	def addEnteredString(self,enteredString,methodOfEntry,numberOfClicks,categoryStructure):
		timestamp = int(datetime.now().timestamp())
		self.addEntryToCollection("ENTERED_STRINGS",
			{"TIMESTAMP":timestamp,
			"STRING":enteredString,
			"ENTRY_METHOD":methodOfEntry,
			"NUM_CLICKS":numberOfClicks,
			"CATEGORY_STRUCTURE":categoryStructure}
			)

	def getHighestClickString(self):
		print (1)

def testEmojiDb():
	#on master category select
	#Get subcategories(masterCategory)
	#For subcategoryName in subcategories:
		#displayIcon = Get subcategoryIconEmoji(subcategoryName)
	# activeSubcatgeory = subCategoies[0]
	#keyboardEmojis = getEmojis(activeSubcategory)



	emojiDber = emojiDatabaseHandler()
	emojiDber.dropAllCollections()
	# selectedCategory = "Tosssp"

	# newSubcategoryNames = emojiDber.getSubCategories(selectedCategory)
	# # print (newSubcategoryNames)
	# for subCategory in newSubcategoryNames:
	# 	subCategoryIcon = emojiDber.getCategoryIcon(subCategory)
	# activeSubCategory = newSubcategoryNames[-1]
	# newKeyboardEmojis = emojiDber.getEmojisOfCategory(activeSubCategory)
	# print (newKeyboardEmojis)
	# emojiDber.dropCollection("CATEGORIES")
	# emojiDber.createTables()

	testEmoji = "2"
	# translation = "ele"
	# language = "English"

	# translation = "hi"
	# language = "German"

	# emojiDber.addEmojiTranslation(testEmoji,translation,language)
	# print (emojiDber.getEmojiTranslations("4"))
	# emojiDber.printAllEntries("EMOJI_TRANSLATIONS")

	category = "middle"
	subCategory = "top"

	# emojiDber.assignCategoryToEmoji(testEmoji,category)
	# emojiDber.assignCategoryToEmoji(testEmoji,subCategory)

	# print (emojiDber.getEmojisOfCategory(subCategory))

	# emojiDber.printAllEntries("EMOJI_SUBCATEGORIES")

	# emojiDber.addSubCategory(category,subCategory)
	emojiDber.printAllEntries("CATEGORIES")

	# print (emojiDber.getSubCategories(category))

	# emojiDber.assignIconToCategory(testEmoji,category)
	# print (emojiDber.getCategoryEmoji(category))

	# emojiDber.printAllEntries("CATEGORY_EMOJIS")
	# emojiDber.printAllEntries("ENTERED_STRINGS")

# testEmojiDb()