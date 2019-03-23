from bokeh.models import ColumnDataSource, CustomJS
from bokeh.plotting import figure
from bokeh.models.glyphs import Text, Circle
from bokeh.io import curdoc, show
from bokeh.events import Tap, DoubleTap
from bokeh.layouts import column, row
from bokeh.models.widgets import TextInput, Button, AutocompleteInput, DataTable, TableColumn, Div
from bokeh.models.tools import HoverTool

import numpy as np
import os

from emojiDbHandler import emojiDatabaseHandler
emojiDber = emojiDatabaseHandler()

def getEmojiAudioFilename(emoji,language):
	return emoji + " " + language + ".mp3"

class emojiPicker:

	def __init__(self):
		self.setupVariables()
		self.createGui()

		self.loadEmojis()

	def setupVariables(self):
		self.keyboardHeight = 650
		self.keyboardWidth = 1200

		self.categoryClickIndex = 0

		self.colWidth = 100
		self.colHeight = self.keyboardHeight
		self.rowHeight = 120

		self.rowWidth = self.keyboardWidth + 2 * self.colWidth

		#keyboard spacing variables
		self.midRowXOffset = .2
		self.keyboardYOffset = .5

		self.keyboardYSpacing = 1
		self.keyBoardXSpacing = 1

		self.TOOLTIPS = """<div>@names</div>"""
		self.TOOLTIPS =  """<div class="btn-group">
			  <button>@names 🔊</button>
			  <button>Schadenfreude 🔊</button>
			  <button>⻄⻇ 🔊</button>
			</div> """

		# var audio = new Audio('emojiMessenger/static/audio.mp3');
		self.filename = "audio.mp3"
		self.playSound = CustomJS(args=dict(filename = self.filename), code = 
			"""
			var audio = new Audio('emojiMessenger/static/'.concat(filename));
			audio.play();
			"""
			)

	def loadEmojis(self):
		self.sessionId = emojiDber.getSessionId()
		self.friendId = emojiDber.checkForUnmatchedFriendId(self.sessionId)

		#main category
		self.mainCategoryNames = emojiDber.getMasterCategories()[1:]
		mainCategoryIcons = emojiDber.getSubCategoriesIcons("MASTER",self.mainCategoryNames)
		self.updateEmojiFigure("Main","Column",mainCategoryIcons)

		#pick the first main category
		self.activeMainCategory = self.mainCategoryNames[0]
		subCategories = emojiDber.getSubCategories(self.activeMainCategory)
		subCategoryIcons = emojiDber.getSubCategoriesIcons(self.activeMainCategory,subCategories)
		self.updateEmojiFigure("Sub","Column",subCategoryIcons)

		#pick the first subcategory
		self.activeSubCategory = subCategories[0]

		#get suggested emojis
		suggestedEmojis = emojiDber.getRelevantEmojis(self.activeMainCategory)
		self.updateEmojiFigure("Suggested","Row",suggestedEmojis)

		#get emojis to display on the keyboars
		subCategoryEmojis = emojiDber.getCategoryTopEmojis(self.activeSubCategory)

		#fill in the difference with main cateogry emojis
		numSubEmojis = len(subCategoryEmojis)
		mainCategoryEmojies = emojiDber.getCategoryTopEmojis(self.activeMainCategory,NUM_TO_GET = 26 - numSubEmojis)
		keyboardEmojisDict = {**subCategoryEmojis,**mainCategoryEmojies}

		self.updateKeyboardFigure(keyboardEmojisDict)

	def updateEmojiFigure(self,figureName,figureType,emojisDict):
		newData = self.createCategoryGlyphSource(emojisDict,figureType)
		self.gui.select_one({"name":figureName}).data = newData

	def updateKeyboardFigure(self,emojisDict):
		newNames = list(emojisDict.keys())
		newEmojis = list(emojisDict.values())

		numEmojis = len(newNames)
		if numEmojis < 26:
			diff = 26 - numEmojis
			newNames += [""] * diff
			newEmojis += [""] * diff

		keyboardSourceDict = (self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data
		keyboardSourceDict["names"] = newNames
		keyboardSourceDict["text"] = newEmojis
		(self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data = keyboardSourceDict

	def createCategoryGlyphSource(self,categoriesDict,figureType):
		categoryEmojies = list(categoriesDict.values())
		categoryNames = list(categoriesDict.keys())
		numCategories = len(categoriesDict.keys())
		indices = range(1,1+numCategories)

		categoryFills = [0] * numCategories

		categoryXs = [0] * numCategories
		categoryYs = range(numCategories)
		if figureType == "Row":
			categoryXs, categoryYs = categoryYs,categoryXs
		else:
			categoryFills[-1] = 1

		categoryGlyphSourceDict = dict(x=categoryXs, y=categoryYs, text=categoryEmojies,names = categoryNames,fills = categoryFills,indices=indices)
		return categoryGlyphSourceDict

	def createEmojiFigure(self,figureType,name):
		#creates either a row or column to display emojies in
		numCategories = 10
		if figureType == "Column":
			height = self.colHeight
			width = self.colWidth
			xRange = (-.5,.5)
			yRange = (-.5,numCategories-.5)
			yOffset = 20

		else:
			height = self.rowHeight
			width = self.rowWidth
			xRange = (-.5,numCategories-.5)
			yRange = (-.4,.6)
			yOffset = 20

		categoriesFigure = figure(title = "Title",
			plot_height = height, plot_width = width,
			x_range=xRange,y_range=yRange,
			toolbar_location = None,tools = "")

		categoriesFigure.axis.visible = False
		categoriesFigure.grid.visible = False

		categorySourceDict = dict(x=[], y=[], text=[],names = [],fills = [],indices=[])

		# categorySourceDict = self.createCategoryGlyphSource(categoriesDict,figureType)
		categorySource = ColumnDataSource(categorySourceDict,name = name)

		#text glyph to display emojies
		categoriesGlyph = Text(x="x", y="y", text="text", angle=0,y_offset=yOffset,
			text_color="black",text_alpha = 1,
			text_font_size='35pt',text_align = "center")

		categoriesFigure.add_glyph(categorySource, categoriesGlyph)

		if figureType == "Row":
			categoryIndexText =  Text(x="x", y="y", text="indices", angle=0,y_offset=-10,x_offset= -50,
				text_color="black",text_alpha = 1,
				text_font_size='20pt',text_align = "center")
			categoriesFigure.add_glyph(categorySource,categoryIndexText)

		#hidden circle glyph used to allow hovertool to work to show tooltips
		categoryCircleGlyph = Circle(x="x", y="y",radius=.45,fill_alpha = 0,line_alpha = "fills")
		circleGlyph = categoriesFigure.add_glyph(categorySource, categoryCircleGlyph, name = "circles")
		#create hover tool and add it to figure
		categoryHoverer = HoverTool(renderers=[circleGlyph], tooltips=self.TOOLTIPS)
		categoriesFigure.add_tools(categoryHoverer)

		return categoriesFigure

	def mainCategorySelectCallback(self,event):
		self.categoryClickIndex += 1
		x,y = (event.x, event.y)
		index = int(y)

		selectedCategory = self.mainCategoryNames[index]
		self.activeMainCategory = selectedCategory

		#update the selected category indicator		
		newFills = [0] * len(self.mainCategoryNames)
		newFills[index] = 1
		self.gui.select_one({"name":"Main"}).data["fills"] = newFills

		#update sub categories
		subCategories = emojiDber.getSubCategories(self.activeMainCategory)
		subCategoryIcons = emojiDber.getSubCategoriesIcons(selectedCategory,subCategories)
		self.updateEmojiFigure("Sub","Column",subCategoryIcons)

		#pick the first new subcategory
		self.activeSubCategory = subCategories[0]
		subCategoryEmojis = emojiDber.getCategoryTopEmojis(self.activeSubCategory)

		#fill in the difference with main cateogry emojis
		numSubEmojis = len(subCategoryEmojis)
		mainCategoryEmojies = emojiDber.getCategoryTopEmojis(self.activeMainCategory,NUM_TO_GET = 26 - numSubEmojis)
		keyboardEmojisDict = {**subCategoryEmojis,**mainCategoryEmojies}

		self.updateKeyboardFigure(keyboardEmojisDict)

	def subCategorySelectCallback(self,event):
		#keep track of how many categories clicked throiugh until an answer found
		self.categoryClickIndex += 1

		x,y = (event.x, event.y)
		index = int(y)
		subCategoryDict = self.gui.select_one({"name":"Sub"}).data

		#update the selected category indicator		
		newFills = [0] * len(subCategoryDict["fills"])
		newFills[index] = 1
		self.gui.select_one({"name":"Sub"}).data["fills"] = newFills

		#change the active categroy abd get the emojis belonging to it
		self.activeSubCategory = subCategoryDict["names"][index]
		subCategoryEmojis = emojiDber.getCategoryTopEmojis(self.activeSubCategory)

		numSubEmojis = len(subCategoryEmojis.keys())

		mainCategoryEmojies = emojiDber.getCategoryTopEmojis(self.activeMainCategory,NUM_TO_GET = 26 - numSubEmojis)
		keyboardEmojisDict = {**subCategoryEmojis,**mainCategoryEmojies}

		self.updateKeyboardFigure(keyboardEmojisDict)

	def suggestedSelectCallback(self,event):
		x,y = (event.x, event.y)
		index = int(x)
		suggestedEmojis = self.gui.select_one({"name":"Suggested"}).data["text"]

		clickedEmoji = suggestedEmojis[index]

		self.text_input.remove_on_change("value",self.textBoxcallback)
		self.text_input.value += (clickedEmoji)
		self.text_input.on_change("value",self.textBoxcallback)

		self.analyzeNgram(self.text_input.value,"tapped")

	def xyCoordsToKeyboardKey(self,x,y):
		"""given an (X,Y) cooridnate, returns the key pressed
		on a qwerty keyboard"""

		rowIndex = int(y/(self.keyboardYSpacing))
		colIndex = (x-(rowIndex*self.midRowXOffset))/self.keyBoardXSpacing
		clickedLetter = self.letters[int(rowIndex)][int(colIndex)]
		return clickedLetter


	def emojiDoubleTapCallback(self,event):
		#called when an emoji keyboard is double tapped
		#updates the suggested categories, but doesn't add it to the textbox
		print (1)

	def emojiTapCallback(self,event):
		#called when an emoji on the keyboard window is single tapped
		x,y = (event.x, event.y)
		index = int(x) + int(y)
		selectedChar = self.xyCoordsToKeyboardKey(x,y)

		emojiSourceData = (self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data
		letterIndex = emojiSourceData["letters"].index(selectedChar)
		selectedEmoji = emojiSourceData["text"][letterIndex]

		self.text_input.remove_on_change("value",self.textBoxcallback)
		self.text_input.value += (selectedEmoji)
		self.text_input.on_change("value",self.textBoxcallback)

		self.filename = "cats.wav"

		self.analyzeNgram(self.text_input.value,"tapped")


	def analyzeNgram(self,ngram,methodOfEntry):
		#get the current category structure
		heirarchy = [self.activeMainCategory,self.activeSubCategory]

		emojiDber.addEnteredString(
			ENTERED_STRING = ngram,
			ENTRY_METHOD = methodOfEntry,
			CLICK_INDEX = self.categoryClickIndex,
			CATEGORY_STRUCTURE = heirarchy,
			SESSION_ID = self.sessionId)

		#reset category click index
		self.categoryClickIndex = 0

		#get new suggestions
		#split the currently entered string
		splitNgram = list(ngram)
		newSuggestionsDict = {}
		for emoji in splitNgram:
			suggestions = emojiDber.getRelevantEmojisFromEmoji(emoji)
			newSuggestionsDict = {**newSuggestionsDict,**suggestions}

		#get suggested emojis
		self.updateEmojiFigure("Suggested","Row",newSuggestionsDict)

	def createMainEmojiWindow(self):
		plot = figure(title="", plot_width=self.keyboardWidth, plot_height=self.keyboardHeight,
			x_range= (-.5,10-.5),y_range = (0,3*self.keyboardYSpacing),
		    h_symmetry=False, v_symmetry=False, min_border=0,
		    toolbar_location=None,tools = "")

		plot.grid.visible = False
		plot.axis.visible = False

		emojiGlyph = Text(x="x", y="y", text="text", angle=0, 
			text_color="black",text_alpha = 1,text_font_size='65pt',text_align = "center")

		source = self.createKeyboardCoordinates()

		plot.add_glyph(source, emojiGlyph,name = "emojis")

		circleGlyph = Circle(x="x", y="y",radius=.5,fill_alpha = 0,line_alpha = 0)
		circGlypher = plot.add_glyph(source, circleGlyph)

		emojiLetterText =  Text(x="x", y="y", text="letters", angle=0,y_offset=-80,x_offset= -40,
			text_color="black",text_alpha = 1,
			text_font_size='20pt',text_align = "center")
		plot.add_glyph(source,emojiLetterText)

		hoverer = HoverTool(renderers=[circGlypher], tooltips=self.TOOLTIPS)
		plot.add_tools(hoverer)

		plot.on_event(Tap,self.emojiTapCallback)
		# plot.on_event(DoubleTap,self.emojiDoubleTapCallback)

		return plot

	def englishBoxCallback(self,attr,old,new):
		#called when someone types something into the english box,
		#gets the suggested emojis and updates the list

		#check if the new value is drastically longer than the old one (indicating autocomplete)
		if (len(new) - len(old)) > 4:
			print ("CLICKED")
			clickedEmoji = new[-1]

			self.text_input.value += (clickedEmoji)
			self.englishInput.value = ""
			return

		suggestedEmojis = emojiDber.getRelevantEmojis(new)
		emojisList = []
		for name,emoji in suggestedEmojis.items():
			entry = name.replace("_"," ") + "   " + emoji
			emojisList.append(entry)

		self.englishInput.completions = emojisList

	def textBoxcallback(self,attr,old,new):
		if (len(old) > len(new)):
			return
		if not new:
			return

		newChar = new[-1]
		if newChar == " ":
			return

		if newChar.isdigit():
			newEmojiIndex = int(newChar)-1
			newEmoji = (self.gui.select_one({"name":"Suggested"})).data["text"][newEmojiIndex]
			self.text_input.remove_on_change("value",self.textBoxcallback)
			self.text_input.value = new[:-1] + newEmoji
			self.text_input.on_change("value",self.textBoxcallback)

		if newChar.isalpha():
			newCharStr = newChar.lower()
			emojiSourceData = (self.gui.select_one({"name":"emojis"})).data_source.data
			typedEmojiIndex = emojiSourceData["letters"].index(newCharStr)
			newEmoji = emojiSourceData["text"][typedEmojiIndex]
			self.text_input.remove_on_change("value",self.textBoxcallback)
			self.text_input.value = new[:-1] + newEmoji
			self.text_input.on_change("value",self.textBoxcallback)

		self.analyzeNgram(self.text_input.value,"typed")

	def createKeyboardCoordinates(self):
		#rectangle window

		topRowXs, topRowYs = list(range(10)),[2*self.keyboardYSpacing + self.keyboardYOffset]*10
		topRowLetters = ["q","w","e","r","t","y","u","i","o","p"]

		midRowXs, midRowYs = list(np.linspace(self.midRowXOffset,9-self.midRowXOffset,9)), [self.keyboardYSpacing + self.keyboardYOffset]*9
		midRowLetters = ["a","s","d","f","g","h","j","k","l"]

		lowRowXs, lowRowYs = list(np.linspace(2*self.midRowXOffset,7-3*self.midRowXOffset,7)),[self.keyboardYOffset]*7
		lowRowLetters = ["z","x","c","v","b","n","m"]
		self.letters = [lowRowLetters,midRowLetters,topRowLetters]
		xCoords = topRowXs + midRowXs + lowRowXs
		yCoords = topRowYs + midRowYs + lowRowYs
		letters = topRowLetters + midRowLetters + lowRowLetters

		self.numCoords = len(xCoords)

		emojis = [""] * self.numCoords
		names = [""] * self.numCoords
		source = ColumnDataSource(dict(x=xCoords, y=yCoords, text=emojis,names = names,letters = letters))
		return source

	###CHAT BOX 

	def createChatBox(self):
		#creates a datatable to show messages
		data = dict(sender=[],message=[])
		source = ColumnDataSource(data)

		columns = [
		        TableColumn(field="sender", title="From"),
		        TableColumn(field="message", title="Message"),
		    ]

		chatBox = DataTable(source=source, columns=columns,
			width=self.keyboardWidth, height=200)
		return chatBox

	def createMessageWindow(self):
		messageWindow = column([],css_classes=["message-box"],width = self.keyboardWidth - 300,height = 400)
		return messageWindow

	def sendMessage(self):
		#posts a message to the db and clears the text box, updates the chat window
		currentMessage = self.text_input.value

		emojiDber.postEnteredMessage(MESSAGE = currentMessage,SESSION_ID = self.sessionId)
		self.updateChatBox("You",currentMessage)

	def createSentDiv(self,message):
		return Div(text=message,height=30,width=self.keyboardWidth-400,css_classes = ["sent-speech-bubble"])

	def createReceivedDiv(self,message):
		return Div(text=message,height=30,width=self.keyboardWidth-400,css_classes = ["received-speech-bubble"])

	def updateChatBox(self,sender,newMessage):
		if sender == "You":
			newDiv = self.createSentDiv(newMessage)
		else:
			newDiv = self.createReceivedDiv(newMessage)

		self.messageWindow.children.append(newDiv)

		# chatBoxSource = self.chatBox.source.data
		# chatBoxSource["sender"].append(sender)
		# chatBoxSource["message"].append(newMessage)
		# self.chatBox.source.data = chatBoxSource



		self.text_input.value = ""



	def getReceivedMessages(self):
		#check if there's a friend id
		self.friendId = emojiDber.checkForUnmatchedFriendId(self.sessionId)

		#if its not found, return and try again later
		if not self.friendId: return

		unreadMessages = emojiDber.getUnreadMessages(SESSION_ID = self.friendId)

		for message in unreadMessages:
			messageText = message["MESSAGE"]
			messageTime = message["TIMESTAMP"]
			self.updateChatBox("Them",messageText)

			emojiDber.incrementMessageRead(SESSION_ID=self.friendId,TIMESTAMP = messageTime)

	def createGui(self):
		# self.chatBox = self.createChatBox()
		self.messageWindow = self.createMessageWindow()
		headerDiv = Div(text="<link rel='stylesheet' type='text/css' href='templates/styles.css'>")

		self.createKeyboardCoordinates()

		self.englishInput = AutocompleteInput(value = "",title = "English:",completions = ["bath","bathtub"])
		self.englishInput.on_change("value",self.englishBoxCallback)

		self.text_input = TextInput(value="", title="Message:",width = self.keyboardWidth - 300)
		self.text_input.on_change("value",self.textBoxcallback)

		sendButton = Button(label="↩",button_type = "primary")
		sendButton.on_click(self.sendMessage)
		self.suggestedCategoryRow = self.createEmojiFigure("Row","Suggested")
		self.suggestedCategoryRow.on_event(Tap,self.suggestedSelectCallback)

		self.suggestedCategoryRow.title.text = "💡"
		self.suggestedCategoryRow.title.text_font_size = "20pt"

		mainCategoryFigure = self.createEmojiFigure("Column","Main")
		mainCategoryFigure.title.text = "🐘📦"
		mainCategoryFigure.title.text_font_size = "30pt"
		mainCategoryFigure.on_event(Tap,self.mainCategorySelectCallback)
		mainCategoryFigure.js_on_event(DoubleTap,self.playSound)

		subCategoryFigure = self.createEmojiFigure("Column","Sub")
		subCategoryFigure.title.text = "🥖📦"
		subCategoryFigure.title.text_font_size = "30pt"
		subCategoryFigure.name = "sub"
		subCategoryFigure.on_event(Tap,self.subCategorySelectCallback)

		self.emojiKeyboard = self.createMainEmojiWindow()
		self.emojiKeyboard.title.text = "⌨"
		self.emojiKeyboard.title.text_font_size = "30pt"
		self.gui = column(
			headerDiv,
			self.messageWindow,
			row(self.englishInput,self.text_input,sendButton),
			self.suggestedCategoryRow,
			row(self.emojiKeyboard,subCategoryFigure,mainCategoryFigure)
		)

	def showGui(self):
		curdoc().add_root(self.gui)
		curdoc().add_periodic_callback(self.getReceivedMessages,1000)
		curdoc().on_session_destroyed(self.destroySession)
		curdoc().title = "Emoji Messenger"
		show(self.gui)

	def destroySession(self,session_context):
		emojiDber.deactivateSessionId(self.sessionId,self.friendId)
		print ("Session closed")

def testEmojiPicker():
	eP = emojiPicker()
	eP.showGui()

# testEmojiPicker()