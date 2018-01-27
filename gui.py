# GUI

# Import libraries
import matplotlib 
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from tkinter import *
from tkinter import filedialog
import time
import os

# Import functions

import processClickTrains
import saveFunctions


def open_file():
	
	root.fileName = filedialog.askopenfilename( filetypes = (("AQUAclick data file","*.csv"),("All files","*.*")))
	fileName.set(str(root.fileName[-60:]))
	root.update()

	return fileName, root.fileName

def save_dir():

	root.saveDir = filedialog.askdirectory()
	saveDir.set(root.saveDir[-60:])
	root.update()

	return saveDir, root.saveDir

def classify():

	# Optain basic parameters
	classLabel = varClassLabel.get()
	csv = varCsv.get()
	plots = varPlots.get()
	sounds = varSounds.get()
	errorDetected = 0

	# Check if all necessary inputs are available

	if entryStr.get() != "":

		try:

			classLabel = float(entryClassManual.get())

			if classLabel <= 0 or classLabel >= 1:

				labelText.set("ERROR: Entered threshold not between 0 and 1 in decimal point format.")
				root.update()
				errorDetected = 1

		except ValueError:

			labelText.set("ERROR: Entered threshold is not a valid number. Use decimal point format.")
			root.update()
			errorDetected = 1

	if ((fileName.get() == "None" or saveDir.get() == "None") or (fileName.get() == "" or saveDir.get() == ""))  and errorDetected == 0:

		labelText.set("ERROR: AQUAclick data and/or output folder not selected.")
		errorDetected = 1
		root.update()

	elif classLabel == 0 and errorDetected == 0:

		labelText.set("ERROR: Classification level not selected.")
		errorDetected = 1
		root.update()

	if errorDetected == 0:

		# All necessary inputs are available! Start processing click trains!

		# Set positive threshold

		positiveThreshold, classLevel = set_positiveThreshold(classLabel)

		# Set path
		root.saveDirPath = root.saveDir + "\\" + str(os.path.split(root.fileName)[1][:-4])

		# Load and extract click trains

		labelText.set("Extracting Click Trains...")
		root.update()

		inputData, timeInfo = processClickTrains.load_data(root.fileName)
		clickTrains = processClickTrains.extract_click_trains(inputData)

		labelText.set("Done: Extracted Click Trains ")
		root.update()

		time.sleep(1)

		# Preprocess click trains for classification

		labelText.set("Preprocessing Click Trains...")
		root.update()

		processedClickTrains = processClickTrains.preprocess_click_trains(clickTrains)

		labelText.set('Done: Preprocessing Click Trains')
		root.update()

		time.sleep(1)

		# Classify click trains

		labelText.set('Making Predictions/Classifying... ')
		root.update()

		classifiedClickTrains = processClickTrains.classify_click_trains(processedClickTrains, positiveThreshold)

		labelText.set('Done: Prediction/Classification')
		root.update()

		time.sleep(1)

		saveFunctions.save_txt_file(classifiedClickTrains, root.saveDirPath, classLevel)

		labelText.set('Done: Saved Click Train Data.txt...')

		time.sleep(1)

		labelText.set('Waiting to run...')
		root.update()

		# SAVE CSV FILES

		if csv != 0:

			saveFunctions.save_csv_files(classifiedClickTrains, root.saveDirPath, csv)

			labelText.set('Done: Saved csv-files...')
			root.update()

			labelText.set('Waiting to run...')
			root.update()

		# SAVE CLICK TRAIN PLOTS AND GENERAL RESULTS

		if plots != 0:

			saveFunctions.plot_general_results(classifiedClickTrains, timeInfo, root.saveDirPath)

			labelText.set('Done: Saved general results plots')
			root.update()

			time.sleep(1)

			labelText.set('Waiting to run...')
			root.update()

			if plots == 2:

				saveFunctions.plot_predictions(classifiedClickTrains,timeInfo, root.saveDirPath, 1, root, labelText)

				time.sleep(1)

				labelText.set('Waiting to run...')
				root.update()

			if plots == 3:

				saveFunctions.plot_predictions(classifiedClickTrains,timeInfo, root.saveDirPath, 0, root, labelText)

				labelText.set('Waiting to run...')
				root.update()

		# SAVE SOUND FILES

		if sounds == 1:

			saveFunctions.generate_sounds(classifiedClickTrains, root.saveDirPath, 1, root, labelText, varSoundSetting.get())

			labelText.set('Waiting to run...')
			root.update()

		elif sounds == 2:

			saveFunctions.generate_sounds(classifiedClickTrains, root.saveDirPath, 0, root, labelText, varSoundSetting.get())

			labelText.set('Waiting to run...')
			root.update()

		root.update()

def clear_all():

	varClassLabel.set(0)
	varCsv.set(0)
	varSounds.set(0)
	varPlots.set(0)
	fileName.set("None")
	saveDir.set("None")
	entryStr.set("")
	root.fileName = "None"
	root.saveDir = "None"
	labelText.set('Waiting to run...')
	varSoundSetting.set(1)
	root.update()

def deselect_radio():

	varClassLabel.set(None)
	root.update()

def deselect_entry():

	entryStr.set("")
	root.update()

def set_positiveThreshold(positiveThresholdSetting):

	if positiveThresholdSetting == 1:

		positiveThreshold = 0.8512709140777588
		classLevel = " (Strict: " + str(positiveThreshold) + ")"

	elif positiveThresholdSetting == 2:

		positiveThreshold = 0.5718547701835632
		classLevel = " (Moderate: " + str(positiveThreshold) + ")"

	elif positiveThresholdSetting == 3:

		positiveThresholdSetting = 0.4109937250614166
		classLevel = " (Loose: " + str(positiveThreshold) + ")"

	else:

		positiveThreshold = positiveThresholdSetting
		classLevel = " (Manual: " + str(positiveThreshold) + ")"

	return positiveThreshold, classLevel

def run_GUI():

	# Global variables
	global fileName 
	global saveDir
	global entryClassManual
	global entryStr
	global varClassLabel
	global varCsv
	global varPlots
	global varSounds
	global labelText
	global strSoundSetting
	global varSoundSetting
	global root

	# Menu
	root = Tk()
	menu = Menu(root)
	root.config(menu = menu)

	soundMenu = Menu(menu,tearoff=False)
	aboutMenu = Menu(menu,tearoff=False)
	helpMenu = Menu(menu,tearoff=False)

	strSoundSetting = [StringVar(),StringVar(),StringVar(),StringVar()]
	varSoundSetting = IntVar()
	varSoundSetting.set(1)

	strSoundSetting[0].set("Adaptive click duration")
	strSoundSetting[1].set("Adaptive frequency")
	strSoundSetting[2].set("Adaptive cycles")
	strSoundSetting[3].set("Insert real porpoise click")

	menu.add_cascade(label = "Sound output settings", menu=soundMenu)
	soundMenu.add_checkbutton(label =  strSoundSetting[0].get(), onvalue = 1, variable = varSoundSetting, offvalue=1)
	soundMenu.add_checkbutton(label =  strSoundSetting[1].get(),  onvalue = 2, variable = varSoundSetting, offvalue=2)
	soundMenu.add_checkbutton(label =  strSoundSetting[2].get(),  onvalue = 3, variable = varSoundSetting, offvalue=3)
	soundMenu.add_checkbutton(label =  strSoundSetting[3].get(), onvalue = 4, variable = varSoundSetting, offvalue=4)

	menu.add_cascade(label = "About",menu=aboutMenu)
	menu.add_cascade(label = "Help",menu=helpMenu)

	# Set GUI settings

	root.title("Porpoise Click Train Classifier")
	root.geometry("500x715+5+15")
	root.resizable(0,0)

	# Buttons and labels

	fileName = StringVar()
	saveDir = StringVar()
	fileName.set("None")
	saveDir.set("None")

	labelOpenFile0 = Label(root, text = "File selected: ").grid(row = 1, column = 0, sticky = W,padx=10)
	labelOpenFile = Label(root, textvariable=fileName).grid(row = 1, column = 0, sticky = W,padx=83)
	labelSaveDir0 = Label(root, text = "Folder selected: ").grid(row = 3, column = 0, sticky = W,padx=10)
	labelSaveDir = Label(root, textvariable=saveDir).grid(row = 3, column = 0, sticky = W,padx=98)

	buttonOpenFile = Button(root,text = "Load AQUAclick data (.csv)", command = open_file)
	buttonSaveDir =  Button(root,text = "Select output folder", command = save_dir)
	buttonClassify = Button(root,text = "CLASSIFY DATA", command = classify)
	buttonClearAll = Button(root,text = "Clear All", command = clear_all)

	# Radio buttons and labels

	varClassLabel = IntVar()
	entryStr = StringVar()
	entryStr.set("")
	labelClassLevel = Label(root, text = "Select classification level: ")
	radioClassLevel1 = Radiobutton(root, text = "Strict (Recommended)", variable= varClassLabel, value = 1,command=deselect_entry)
	radioClassLevel2 = Radiobutton(root, text = "Moderate", variable= varClassLabel, value = 2,command=deselect_entry)
	radioClassLevel3 = Radiobutton(root, text = "Loose",variable= varClassLabel, value = 3,command=deselect_entry)
	labelClassManual = Label(root, text="Manual threshold: ")
	entryClassManual = Entry(root,textvariable=entryStr)

	varCsv = IntVar()
	labelCsv = Label(root, text = "Select output classification files to save: ")
	radioCsv1 = Radiobutton(root, text = "Save only positively classified click trains in a .csv-file", variable= varCsv, value = 1)
	radioCsv2 = Radiobutton(root, text = "Save all extracted click trains in a .csv-file", variable= varCsv, value = 2)
	radioCsv3 = Radiobutton(root, text = "Save all classified click trains in a .csv-file with probabilities",variable= varCsv, value = 3)
	radioCsv4 = Radiobutton(root, text = "All of above" ,variable= varCsv, value = 4)

	varPlots = IntVar()
	labelPlots = Label(root, text = "Select output classification plots to save: ")
	radioPlots1 = Radiobutton(root, text = "Save general results only", variable= varPlots, value = 1)
	radioPlots2 = Radiobutton(root, text = "Save general results and positively classified click trains (This may take a while)", variable= varPlots, value = 2)
	radioPlots3 = Radiobutton(root, text = "Save general results and all click trains (This may take a while)", variable= varPlots, value = 3)

	varSounds = IntVar()
	labelSounds = Label(root, text = "Select output click train sounds to save: ")
	radioSounds1 = Radiobutton(root, text = "Save positively classified click train sounds", variable= varSounds, value = 1)
	radioSounds2 = Radiobutton(root, text = "Save all click train sounds", variable= varSounds, value = 2)

	# Grid

	buttonOpenFile.grid(row = 0, column = 0, sticky = W, pady=10,padx=10)
	buttonSaveDir.grid(row = 2, column = 0, sticky = W, pady=10,padx=10)

	labelClassLevel.grid(row = 4,column = 0, sticky = W, pady=10, padx=10)
	radioClassLevel1.grid(row= 5,column = 0, sticky = W, padx=20)
	radioClassLevel2.grid(row= 6,column = 0, sticky = W, padx=20)
	radioClassLevel3.grid(row= 7,column = 0, sticky = W, padx=20)
	labelClassManual.grid(row=8, column=0,sticky = W, padx=20)
	entryClassManual.grid(row=8, column=0,sticky = W, padx=150)

	labelCsv.grid(row = 9,column = 0, sticky = W, pady=10, padx=10)
	radioCsv1.grid(row= 10,column = 0, sticky = W, padx=20)
	radioCsv2.grid(row= 11,column = 0, sticky = W, padx=20)
	radioCsv3.grid(row= 12,column = 0, sticky = W, padx=20)
	radioCsv4.grid(row= 13,column = 0, sticky = W, padx=20)

	labelPlots.grid(row = 14,column = 0, sticky = W, pady=10, padx=10)
	radioPlots1.grid(row= 15,column = 0, sticky = W, padx=20)
	radioPlots2.grid(row= 16,column = 0, sticky = W, padx=20)
	radioPlots3.grid(row= 17,column = 0, sticky = W, padx=20)

	labelSounds.grid(row = 18,column = 0, sticky = W, pady=10, padx=10)
	radioSounds1.grid(row= 19,column = 0, sticky = W, padx=20)
	radioSounds2.grid(row= 20,column = 0, sticky = W, padx=20)

	buttonClassify.grid(row = 21, column = 0, sticky = W, pady=15, padx = 10)
	buttonClearAll.grid(row = 21, column = 0, sticky = W, pady=15, padx = 125)

	labelText = StringVar()
	status = Label(root, textvariable=labelText, bd=1, relief=SUNKEN, anchor=W)
	status.grid(row=22,sticky = W,padx = 10)
	labelText.set('Waiting to run...')

	root.mainloop()


# START GUI!
run_GUI()