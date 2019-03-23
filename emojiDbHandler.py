from pymongo import MongoClient, ASCENDING
from datetime import datetime

class emojiDatabaseHandler:

	def __init__(self):
		self.loadEmojiDatabase()

	def loadEmojiDatabase(self):
		mongoClient = MongoClient('mongodb://localhost:27017/')
		self.emojiDb = mongoClient["emojiDb"]

	def createTables(self):
		self.emojiDb["SUBCATEGORY_EMOJIS"].create_index([
			('SUBCATEGORY', ASCENDING)
			],unique = True)

		self.emojiDb["EMOJIS"].create_index([
			('EMOJI',ASCENDING)
			],unique = True)

		self.emojiDb["EMOJI_TRANSLATIONS"].create_index([
			('EMOJI', ASCENDING),
			("LANGUAGE",ASCENDING)
			],unique = True)

		self.emojiDb["CATEGORIES"].create_index([
			('CATEGORY',ASCENDING),
			('SUBCATEGORY',ASCENDING)
			],unique = True)

		self.emojiDb["ENTERED_STRINGS"].create_index([
			('TIMESTAMP', ASCENDING)
			],unique = True)

		self.emojiDb["EMOJI_MESSAGES"].create_index([
			('SESSION_ID', ASCENDING),
			('TIMESTAMP', ASCENDING)
			],unique = True)

		self.emojiDb["SESSIONS"].create_index([
			('SESSION_ID', ASCENDING)
			],unique = True)

	def dropCollection(self,COLLECTION_NAME):
		self.emojiDb.drop_collection(COLLECTION_NAME)

	def dropAllCollections(self):
		self.dropCollection("SUBCATEGORY_EMOJIS")
		self.dropCollection("EMOJIS")
		self.dropCollection("EMOJI_TRANSLATIONS")
		self.dropCollection("CATEGORIES")
		self.dropCollection("ENTERED_STRINGS")
		self.dropCollection("SESSIONS")
		self.dropCollection("EMOJI_MESSAGES")
		self.createTables()

	def dropUserCollections(self):
		self.dropCollection("ENTERED_STRINGS")
		self.dropCollection("SESSIONS")
		self.dropCollection("EMOJI_MESSAGES")


	def addEntryToCollection(self,COLLECTION_NAME,ENTRY):
		try:
			self.emojiDb[COLLECTION_NAME].insert_one(ENTRY)
			return 1
		except:
			return 0

	def upsertEntryToCollection(self,COLLECTION_NAME,SELECTION_CRITERIA,UPDATE_CRITERIA):
		return self.emojiDb[COLLECTION_NAME].update_one(SELECTION_CRITERIA,UPDATE_CRITERIA, upsert=True)

	def findEntryFromCollection(self,COLLECTION_NAME,ENTRY_CRITERIA,MASK_CRITERIA={"_id":0}):
		return self.emojiDb[COLLECTION_NAME].find_one(ENTRY_CRITERIA,MASK_CRITERIA)
	
	def findManyEntries(self,COLLECTION_NAME,ENTRY_CRITERIA,MASK_CRITERIA={"_id":0}):
		return self.emojiDb[COLLECTION_NAME].find(ENTRY_CRITERIA,MASK_CRITERIA)

	def printAllEntries(self,COLLECTION_NAME):
		for entry in self.emojiDb[COLLECTION_NAME].find({},{"_id":0}):
			print (entry)

	#EMOJI ADDING
	def addEmoji(self,EMOJI,NAME,POPULARITY = 0):
		#adds an emoji to the known list of emojis
		self.addEntryToCollection("EMOJIS",
			{"EMOJI":EMOJI,"NAME":NAME,"POPULARITY":POPULARITY})

	def addEmojiToSubcategory(self,SUBCATEGORY,EMOJI):
		#updates the list of emojis belonging to a subcategory OR
		#adds a new entry and sets the icon to the new emoji if that subcategory doesn't exist yet 
		selectionCriteria = {"SUBCATEGORY" : SUBCATEGORY}
		updateCriteria = {"$push" : {"EMOJIS":EMOJI} }
		self.upsertEntryToCollection("SUBCATEGORY_EMOJIS",selectionCriteria,updateCriteria)

	#CATEGORY ADDING
	def associateMasterSubCategory(self,CATEGORY,SUBCATEGORY,EMOJI):
		return self.addEntryToCollection("CATEGORIES",{"CATEGORY" : CATEGORY,"SUBCATEGORY" : SUBCATEGORY,"ICON":EMOJI})

	#TRANSLATION
	def addEmojiTranslation(self,EMOJI,LANGUAGE,TRANSLATION):
		self.addEntryToCollection("EMOJI_TRANSLATIONS",
			{"EMOJI":EMOJI,"LANGUAGE":LANGUAGE,"TRANSLATION":TRANSLATION})

	def getEmojiName(self,EMOJI):
		emojiName =  self.findEntryFromCollection("EMOJIS",{"EMOJI":EMOJI},{"NAME":1,"_id":0})
		if emojiName: return emojiName["NAME"]
		else: return ""

	def getMasterCategories(self):
		return self.findManyEntries("CATEGORIES",{}).distinct("CATEGORY")

	def getSubCategoriesIcons(self,CATEGORY,SUBCATEGORIES):
		#returns a list of emojis given a list of categories
		icons = {}
		for subCategory in SUBCATEGORIES:
			icon = self.findEntryFromCollection("CATEGORIES",
				{"CATEGORY":CATEGORY,"SUBCATEGORY": subCategory},
				{"ICON":1,"_id":0})["ICON"]
			icons[subCategory] = icon

		return icons

	def getCategoryTopEmojis(self,SUBCATEGORY,NUM_TO_GET = 26):
		includedEmojis = self.findEntryFromCollection("SUBCATEGORY_EMOJIS",
			{"SUBCATEGORY":SUBCATEGORY},
			{"EMOJIS":1,"_id":0})

		if not includedEmojis: return {}

		emojisList = includedEmojis["EMOJIS"]
		if len(emojisList) > NUM_TO_GET: emojisList = emojisList[:NUM_TO_GET]

		emojisDict = {}
		for emoji in emojisList:
			name = self.getEmojiName(emoji)
			emojisDict[name] = emoji

		return emojisDict

	def getRelevantEmojis(self,textString):
		#given a text string, finds emojis with names who match the category
		relevantCategoryEmojis = self.findManyEntries("CATEGORIES",
			{"SUBCATEGORY" :{"$regex": textString.lower()}},
			{"ICON":1,"SUBCATEGORY":1,"_id":0})

		relevantEmojis = self.findManyEntries("EMOJIS",
			{"NAME":{"$regex" : textString.lower()}},
			{"EMOJI":1,"NAME":1,"_id":0})

		outputDict = {}
		for categoryEmoji in relevantCategoryEmojis:
			if len(outputDict) > 9: break

			outputDict[categoryEmoji["SUBCATEGORY"]] = categoryEmoji["ICON"]

		for emoji in relevantEmojis:
			if len(outputDict) > 9: break
			outputDict[emoji["NAME"]] = emoji["EMOJI"]

		return outputDict

	def getRelevantEmojisFromEmoji(self,EMOJI):
		emojiName = self.getEmojiName(EMOJI)
		if emojiName: return self.getRelevantEmojis(emojiName)
		else: return {}

	def getSubCategoryIcon(self,CATEGORY,SUBCATEGORY):
		return self.findEntryFromCollection("CATEGORIES",
			{"CATEGORY" : CATEGORY, "SUBCATEGORY":SUBCATEGORY},
			{"ICON":1,"_id" : 0})

	def getSubCategories(self,CATEGORY,NUM_TO_GET=10):
		subCategories = self.findManyEntries("CATEGORIES",
			{"CATEGORY":CATEGORY},
			{"SUBCATEGORY":1,"_id":0}).distinct("SUBCATEGORY")[:NUM_TO_GET]

		return subCategories

	#ENTERED STRINGS
	def addEnteredString(self,ENTERED_STRING,ENTRY_METHOD,CLICK_INDEX,CATEGORY_STRUCTURE,SESSION_ID):
		timestamp = datetime.now().timestamp()

		self.addEntryToCollection("ENTERED_STRINGS",
			{"TIMESTAMP":timestamp,
			"STRING":ENTERED_STRING,
			"ENTRY_METHOD":ENTRY_METHOD,
			"NUM_CLICKS":CLICK_INDEX,
			"CATEGORY_STRUCTURE":CATEGORY_STRUCTURE,
			"SESSION_ID" : SESSION_ID,}
			)

	def postEnteredMessage(self,MESSAGE,SESSION_ID):
		timestamp = datetime.now().timestamp()
		self.addEntryToCollection("EMOJI_MESSAGES",
			{"MESSAGE" : MESSAGE,
			"TIMESTAMP" : timestamp,
			"SESSION_ID" : SESSION_ID,
			"READ" : 0})

	def getUnreadMessages(self,SESSION_ID):
		messagesCursor = self.findManyEntries("EMOJI_MESSAGES",
			{"SESSION_ID":SESSION_ID,"READ":0},{"MESSAGE":1,"TIMESTAMP":1,"_id":0})
		return list(messagesCursor)

	def incrementMessageRead(self,SESSION_ID,TIMESTAMP):
		selectionCriteria = {
			"SESSION_ID":SESSION_ID,
			"TIMESTAMP" :TIMESTAMP
			}

		updateCriteria = {"$inc" : {"READ": 1}}
		self.upsertEntryToCollection("EMOJI_MESSAGES",selectionCriteria,updateCriteria)

	#SESSIONS
	def generateSessionId(self):
		return int(datetime.now().timestamp())

	def getSessionId(self):
		#called on login, gives the person logging in a new session id
		newSessionId = self.generateSessionId()

		#check if there are any un-matched IDs (that are active)
		unMatchedId = self.findEntryFromCollection("SESSIONS",
			{"FRIEND_SESSION_ID":0,"SESSION_ID_ACTIVE":1},
			{"SESSION_ID":1,"_id":0})

		#if an unmached id is found
		if unMatchedId:
			friendId = unMatchedId["SESSION_ID"]
			self.addEntryToCollection("SESSIONS",
				{"SESSION_ID":newSessionId,"SESSION_ID_ACTIVE":1,"FRIEND_SESSION_ID":friendId})

			self.upsertEntryToCollection("SESSIONS",
				{"SESSION_ID":friendId},
				{"$set":{"FRIEND_SESSION_ID":newSessionId}})


		#otherwise add this one as un-matched and wait for someone else to match it
		else:
			self.addEntryToCollection("SESSIONS",
				{"SESSION_ID":newSessionId,"SESSION_ID_ACTIVE":1,"FRIEND_SESSION_ID":0})

		return newSessionId

	def checkForUnmatchedFriendId(self,SESSION_ID):
		#check to see if your session Id has been assigned a friend
		unMatchedId = self.findEntryFromCollection("SESSIONS",
			{"SESSION_ID":SESSION_ID,"SESSION_ID_ACTIVE":1},
			{"FRIEND_SESSION_ID":1,"_id":0})

		#if the friend ID is not 0
		friendId = unMatchedId["FRIEND_SESSION_ID"]
		return friendId

	def deactivateSessionId(self,SESSION_ID,FRIEND_SESSION_ID):
		#removes the active flag from the session id and resets the friend id of its friend so it can be matched again
		self.upsertEntryToCollection("SESSIONS",
			{"SESSION_ID":SESSION_ID},
			{"$set":{"SESSION_ID_ACTIVE":0}})

		#if it had a friend id, reset that friend's friend id so they can rematch
		if FRIEND_SESSION_ID: self.upsertEntryToCollection("SESSIONS",
			{"SESSION_ID":FRIEND_SESSION_ID},
			{"$set":{"FRIEND_SESSION_ID":0}})

	def getEmojiTranslations(self,EMOJI):
		return self.findOneEntry("EMOJI_TRANSLATIONS",
			{"EMOJI":emoji},
			{"_id":0,"EMOJI":0}
			)

def testEmojiDb():
	emojiDber = emojiDatabaseHandler()

	bigCategories = emojiDber.findManyEntries("CATEGORIES",
		{}).distinct("CATEGORY")
	print (bigCategories)

	# bigCategories = emojiDber.findManyEntries("SUBCATEGORY_EMOJIS",
	# 	{"EMOJIS.12": { "$exists" : True }})

	# numCategories = bigCategories.count()


	categories = {
		'activity' : ['music','activity','blow','call','cut','change','hit','make','create','set','speak','talk','utter','cover','withdraw','remove','take','plunge','touch','place','telecasting','preparation','verbalise','verbalize','business','astrology','star divination'],
		'flags' : ['flags'],
		'foods' : ['cookery','preparation','foods'],
		'nature' : ['nature','shell','herbaceous plant'],
		'objects' : ['car','tv','herbaceous plant','structure','video','sound','ball','objects','war machine','armed forces','military machine','armed services','military'],
		'people' : ['people','individual','mortal','person','somebody','someone','soul','adult female'],
		'places' : ['places','place'],
		'symbols' : ['symbols'],
	}
 	
	# print (numCategories)

	# for category in bigCategories:
		# print (category["SUBCATEGORY"])

	# namedEmojis = emojiDber.findEntryFromCollection("EMOJIS",
	# 	{"NAME": "eg"})

	# print (namedEmojis)

	#startup routine for emoji keyboard
	# emojiDber.getSessionId()

	# #populate master categories selector
	# masterCategoryNames = emojiDber.getMasterCategories()[1:]
	# print (masterCategoryNames)

	# # masterCategoryIcons = emojiDber.getSubCategoriesIcons("MASTER",masterCategoryNames)
	# # # print (masterCategoryIcons)

	# #pick the first subcategory
	# selectedCategory = masterCategoryNames[0]
	# subCategories = emojiDber.getSubCategories(selectedCategory)

	# # print (subCategories)

	# # get the subcategory icons
	# subCategoryIcons = emojiDber.getSubCategoriesIcons(selectedCategory,subCategories)
	# # print (subCategoryIcons)

	# selectedSubCategory = subCategories[0]
	# print (selectedSubCategory)

	# subCategoryEmojis = emojiDber.getRelevantEmojis("bath")

	# relevantSubs = emojiDber.getRelevantEmojis("sy")
	# print (relevantSubs)

	# CATEGORY = "MAIN"
	# SUBCATEGORY = "TEST0"
	# EMOJI = "1"
	# NAME = "One"
	# # TRANSLATION = "Hello1"
	# LANGUAGE = "ENGLISH"

	# emojiDber.addEmojiTranslation(EMOJI,LANGUAGE,TRANSLATION)

	# print (emojiDber.associateMasterSubCategory(CATEGORY,SUBCATEGORY))

	# emojiDber.addEmojiToSubcategory(SUBCATEGORY,EMOJI)
	# # emojiDber.addEmoji(EMOJI,NAME)

	# emojiDber.printAllEntries("EMOJI_TRANSLATIONS")
	# emojiDber.printAllEntries("CATEGORIES")
	# emojiDber.printAllEntries("EMOJIS")
	# emojiDber.printAllEntries("SUBCATEGORY_EMOJIS")
	# emojiDber.printAllEntries("ENTERED_STRINGS")

# testEmojiDb()