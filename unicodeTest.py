#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# sourceFileName = "emoji-data.txt"
# sinkFileName = "sink.txt"
# parseUnicodeFile(sourceFileName,sinkFileName)

def loadCategoryDict(fileName):
	categoryDict = {}
	with open(fileName,"r",encoding = "utf-8") as categoryFile:
		for line in categoryFile.readlines():
			name,emoji = line.rstrip("\n").split("\t")
			categoryDict[name] = emoji

		categoryFile.close()
	return categoryDict

# # def loadCategories():
# mainCategories = loadCategoryDict("mainCategories.txt")
# mainCategoryNames = list(mainCategories.keys())
# jobCategories = loadCategoryDict("jobsCategories.txt")
# facesCategories = loadCategoryDict("facesCategories.txt")

# subCategories = {
# 	"Faces": jobCategories,
# 	"Jobs" : facesCategories,
# 	"Paths" : mainCategories,
# 	"Landmarks" : jobCategories,
# 	"Geographic features" : facesCategories,
# 	"Sports" : mainCategories,
# 	"Stores" : jobCategories,
# 	"Weapons" :facesCategories
# 	}

# activeCategory = "Faces"
# activeSubCategoriesDict = subCategories[activeCategory]

# emojiFilename = "sink.txt"
# names, emojiList = readEmojiFile(emojiFilename,20)

from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn

import numpy as np

from bokeh.models import ColumnDataSource, Plot, LinearAxis, Grid, CustomJS
from bokeh.plotting import figure
from bokeh.models.glyphs import Text, Circle
from bokeh.io import curdoc, show
from bokeh.events import Tap, DoubleTap
from bokeh.layouts import column, row
from bokeh.models.widgets import TextInput, Button, Div
from bokeh.models.tools import HoverTool

import os

# from mongodbHandler import emojiDatabaseHandler
# emojiDber = emojiDatabaseHandler()


class emojiPicker:

	def __init__(self):
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

		#for running as bokeh server or python
		try:
			(os.listdir("emojiPicker"))
			emojiFilename = os.path.join("emojiPicker","emojis","sink.txt")
		except:
			emojiFilename = os.path.join("emojis","sink.txt")

		self.readEmojiFile(emojiFilename)


		self.TOOLTIPS = """<div>@names</div>"""
		self.TOOLTIPS =  """<div class="btn-group">
			  <button>@names 🔊</button>
			  <button>Schadenfreude 🔊</button>
			  <button>⻄⻇ 🔊</button>
			</div> """

		self.playSound = CustomJS(args=dict(), code = 
			"""
			var audio = new Audio('audio.mp3');
			audio.play();
			"""
			)

		self.createGui()

	def readLinesToDictionary(self,fileObj,numLinesToRead):
		emojiDict = {}
		readEmojiLine = lambda line : line.rstrip("\n").split("\t")

		for lineInd in range(numLinesToRead):
			line = fileObj.readline()
			name,emoji = readEmojiLine(line)
			emojiDict[name] = emoji
		return emojiDict

	def readEmojiFile(self,emojiFilename):
		names = []
		emojis = u""
		with open(emojiFilename,"r",encoding = "utf-8") as emojiFile:

			self.numSuggestedCatergoriesToRead = 10
			self.masterCategoriesToRead = 3
			subCategoriesToRead = 6
			subSubCategoriesToRead = 26
			self.suggestedCatergoryDict = self.readLinesToDictionary(emojiFile,self.numSuggestedCatergoriesToRead)

			self.mainCategoryDict = self.readLinesToDictionary(emojiFile,self.masterCategoriesToRead)
			self.mainCategoryNames = list(self.mainCategoryDict.keys())

			self.activeMainCategory = self.mainCategoryNames[0]

			self.subCategoriesDict = {}
			for key in self.mainCategoryNames:
				self.subCategoriesDict[key] = self.readLinesToDictionary(emojiFile,subCategoriesToRead)

			self.activeSubCategory = list(self.subCategoriesDict[self.activeMainCategory].keys())[0]

			self.subSubCategoriesDict = {}
			for key in self.mainCategoryNames:
				self.subSubCategoriesDict[key] = {}
				for subKey in self.subCategoriesDict[key].keys():
					self.subSubCategoriesDict[key][subKey] = self.readLinesToDictionary(emojiFile,subSubCategoriesToRead)

			emojiFile.close()
		return

	def createCategoryGlyphSource(self,categoriesDict,figureType):
		categoryEmojies = list(categoriesDict.values())
		categoryNames = list(categoriesDict.keys())
		numCategories = len(categoriesDict.keys())
		indices = range(1,1+numCategories)

		categoryFills = [0] * numCategories
		# activeCategory = 0

		categoryXs = [0] * numCategories
		categoryYs = range(numCategories)
		if figureType == "Row":
			categoryXs, categoryYs = categoryYs,categoryXs
		else:
			categoryFills[-1] = 1

		categoryGlyphSourceDict = dict(x=categoryXs, y=categoryYs, text=categoryEmojies,names = categoryNames,fills = categoryFills,indices=indices)
		return categoryGlyphSourceDict

	def createEmojiFigure(self,categoriesDict,figureType):
		numCategories = len(categoriesDict.keys())
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

		categorySourceDict = self.createCategoryGlyphSource(categoriesDict,figureType)
		categorySource = ColumnDataSource(categorySourceDict)

		#text glyph to display emojies
		categoriesGlyph = Text(x="x", y="y", text="text", angle=0,y_offset=yOffset,
			text_color="black",text_alpha = 1,
			text_font_size='35pt',text_align = "center")

		categoriesFigure.add_glyph(categorySource, categoriesGlyph,name = "emojis")

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

		#database code
		# newSubcategoryNames = emojiDber.getSubCategories(selectedCategory)
		# activeSubCategoriesDict = {}
		# for subCategory in newSubcategoryNames:
		# 	subCategoryIcon = emojiDber.getCategoryIcon(subCategory)
		# 	activeSubCategoriesDict[subCategory] = subCategoryIcon

		# self.activeSubCategory = newSubcategoryNames[-1]
		# newKeyboardEmojis = emojiDber.getEmojisOfCategory(self.activeSubCategory)

		# mainCategorySource = self.mainCategoryFigure.select_one({"name":"emojis"}).data_source
		# newFills = [0] * len(self.mainCategoryNames)
		# newFills[index] = 1
		# mainCategorySource.data["fills"] = newFills


		# activeSubCategoriesDict = self.subCategoriesDict[selectedCategory]
		# subCategoryNames = list(activeSubCategoriesDict.keys())

		# numCategories = len(subCategoryNames)
		# self.activeSubCategory = subCategoryNames[-1]
		
		newCategorySourceDict = self.createCategoryGlyphSource(activeSubCategoriesDict,"Column")
		(self.subCategoryFigure.select_one({"name":"emojis"})).data_source.data = newCategorySourceDict


	def subCategorySelectCallback(self,event):
		self.categoryClickIndex += 1

		x,y = (event.x, event.y)
		index = int(y)

		subCategorySource = self.subCategoryFigure.select_one({"name":"emojis"}).data_source
		newFills = [0] * len(subCategorySource.data["fills"])
		newFills[index] = 1
		subCategorySource.data["fills"] = newFills

		selectedCategory = subCategorySource.data["names"][index]

		activeSubSubCategoriesDict = self.subSubCategoriesDict[self.activeMainCategory][selectedCategory]
		newNames = list(activeSubSubCategoriesDict.keys())
		newEmojis = list(activeSubSubCategoriesDict.values())
		keyboardSourceDict = (self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data
		keyboardSourceDict["names"] = newNames
		keyboardSourceDict["text"] = newEmojis
		(self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data = keyboardSourceDict

		# numCategories = len(activeSubCategoriesDict.keys())

	def updateSuggestedEmojis(self,newSuggestions):
		(self.suggestedCategoryRow.select_one({"name":"emojis"})).data_source.data = newSuggestions

	def xyCoordsToKeyboardKey(self,x,y):
		"""given an (X,Y) cooridnate, returns the key pressed
		on a qwerty keyboard"""

		rowIndex = int(y/(self.keyboardYSpacing))
		colIndex = (x-(rowIndex*self.midRowXOffset))/self.keyBoardXSpacing
		clickedLetter = self.letters[int(rowIndex)][int(colIndex)]
		return clickedLetter

	def selectedCallback(self,event):
		x,y = (event.x, event.y)
		index = int(x) + int(y)
		selectedChar = self.xyCoordsToKeyboardKey(x,y)
		# clickedEmoji = self.activeEmojis[index]

		emojiSourceData = (self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data
		letterIndex = emojiSourceData["letters"].index(selectedChar)
		selectedEmoji = emojiSourceData["text"][letterIndex]

		# self.activeString += clickedEmoji
		self.text_input.remove_on_change("value",self.textBoxcallback)

		self.text_input.value += (selectedEmoji)
		self.text_input.on_change("value",self.textBoxcallback)

		self.analyzeNgram(self.text_input.value,"tapped")

	def analyzeNgram(self,ngram,methodOfEntry):
		heirarchy = [self.activeMainCategory,self.activeSubCategory]

		emojiDber.addEnteredString(
			enteredString = ngram,
			methodOfEntry = methodOfEntry,
			numberOfClicks = self.categoryClickIndex,
			categoryStructure = heirarchy)

		self.categoryClickIndex = 0

		# print (ngram)
		fullNewSuggestionsDict = self.subSubCategoriesDict[self.activeMainCategory][self.activeSubCategory] 
		newSuggestionsKeys = list(fullNewSuggestionsDict.keys())[:10]
		newSuggestionsDict = {}
		for key in newSuggestionsKeys:
			newSuggestionsDict[key] = fullNewSuggestionsDict[key]

		newSuggestionGlyphDict = self.createCategoryGlyphSource(newSuggestionsDict,"Row")

		self.updateSuggestedEmojis(newSuggestionGlyphDict)


		# print (newSuggestions)

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

		plot.on_event(Tap,self.selectedCallback)
		return plot

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
			newEmoji = (self.suggestedCategoryRow.select_one({"name":"emojis"})).data_source.data["text"][newEmojiIndex]
			self.text_input.remove_on_change("value",self.textBoxcallback)
			self.text_input.value = new[:-1] + newEmoji
			self.text_input.on_change("value",self.textBoxcallback)

		if newChar.isalpha():
			newCharStr = newChar.lower()
			emojiSourceData = (self.emojiKeyboard.select_one({"name":"emojis"})).data_source.data
			typedEmojiIndex = emojiSourceData["letters"].index(newCharStr)
			newEmoji = emojiSourceData["text"][typedEmojiIndex]
			self.text_input.remove_on_change("value",self.textBoxcallback)
			self.text_input.value = new[:-1] + newEmoji
			self.text_input.on_change("value",self.textBoxcallback)

		self.analyzeNgram(self.text_input.value,"typed")

	def createKeyboardCoordinates(self):
		#rectangle windw
		# xs,ys = range(dimensions),range(dimensions)

		# xCoords = []
		# yCoords = []
		# self.activeEmojis = []

		# for x in xs:
		# 	for y in ys:
		# 		index =  (x*dimensions + y)
		# 		emoji = self.emojiList[index]
		# 		self.activeEmojis.append(emoji)
		# 		xCoords.append(x)
		# 		yCoords.append(y)

		# source = ColumnDataSource(dict(x=xCoords, y=yCoords, text=self.activeEmojis,names = self.names))

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

		numCoords = len(xCoords)

		emojisDict = self.subSubCategoriesDict[self.activeMainCategory][self.activeSubCategory]
		emojis = list(emojisDict.values())
		names = list(emojisDict.keys())
		source = ColumnDataSource(dict(x=xCoords, y=yCoords, text=emojis,names = names,letters = letters))
		return source

	def createChatBox(self):
		data = dict(sender=[],message=[])
		source = ColumnDataSource(data)

		columns = [
		        TableColumn(field="sender", title="From"),
		        TableColumn(field="message", title="Message"),
		    ]
		chatBox = DataTable(source=source, columns=columns,
			width=self.keyboardWidth, height=200)
		return chatBox

	def sendMessage(self):
		currentMessage = self.text_input.value
		chatBoxSource = self.chatBox.source.data
		sender = "Sender"

		chatBoxSource["sender"].append(sender)
		chatBoxSource["message"].append(currentMessage)
		self.chatBox.source.data = chatBoxSource
		self.text_input.value = ""

	def createGui(self):
		self.chatBox = self.createChatBox()
		self.createKeyboardCoordinates()

		self.text_input = TextInput(value="", title="Label:",width = self.keyboardWidth)
		self.text_input.on_change("value",self.textBoxcallback)

		sendButton = Button(label="↩",button_type = "primary")
		sendButton.on_click(self.sendMessage)
		self.suggestedCategoryRow = self.createEmojiFigure(self.suggestedCatergoryDict,"Row")

		self.suggestedCategoryRow.title.text = "💡"
		self.suggestedCategoryRow.title.text_font_size = "20pt"

		self.mainCategoryFigure = self.createEmojiFigure(self.mainCategoryDict,"Column")
		self.mainCategoryFigure.title.text = "🐘📦"
		self.mainCategoryFigure.title.text_font_size = "20pt"
		self.mainCategoryFigure.on_event(Tap,self.mainCategorySelectCallback)
		self.mainCategoryFigure.js_on_event(DoubleTap,self.playSound)

		self.subCategoryFigure = self.createEmojiFigure(self.subCategoriesDict[self.activeMainCategory],"Column")
		self.subCategoryFigure.title.text = "🥖📦"
		self.subCategoryFigure.title.text_font_size = "20pt"
		self.subCategoryFigure.name = "sub"
		self.subCategoryFigure.on_event(Tap,self.subCategorySelectCallback)

		self.emojiKeyboard = self.createMainEmojiWindow()
		self.emojiKeyboard.title.text = "⌨"
		self.emojiKeyboard.title.text_font_size = "20pt"
		self.gui = column(
			self.chatBox,
			row(self.text_input,sendButton),
			self.suggestedCategoryRow,
			row(self.emojiKeyboard,self.subCategoryFigure,self.mainCategoryFigure)
		)

	def showGui(self):
		curdoc().add_root(self.gui)
		show(self.gui)