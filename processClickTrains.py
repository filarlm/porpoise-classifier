# Load libraries
import os
import pandas
import numpy
from keras.models import model_from_json

class ClickTrain(object):

	def __init__(self,number,data):

		# Basic parameters:
		self.number = number
		self.data = data
		self.time = data[:,0]
		self.cd = data[:,1].copy()
		self.ici = data[:,2].copy()
		self.a130 = data[:,3]
		self.a60 = data[:,4]
		self.ratio = data[:,3]/data[:,4]

		#Misc parameters
		self.len = len(data)
		self.numberPositiveParts = 0
		self.positive = 0
		self.predictions = []
		self.clickPredictions = numpy.array([])
		self.reverbs = numpy.array([])

	def split(self,split):

		self.split = split
		self.numberParts = int(numpy.ceil(self.len/split))
		self.clickTrainParts = []

		for ii in range(0,self.numberParts):

			tmpStartIndex = int(ii*self.split)
			tmpEndIndex = int((ii+1)*self.split)

			if self.len < tmpEndIndex:

				tmpEndIndex = self.len

			tmpClickTrainPart = self.data[tmpStartIndex:tmpEndIndex,:]

			self.clickTrainParts.append(ClickTrainPart(ii, self.number, tmpClickTrainPart))

	def get_reverbs(self):

		self.reverbs = numpy.append(self.reverbs, self.clickTrainParts[0].reverbIndex).astype(int)
		shift = 0

		for ii in range(1,self.numberParts):

			shift = self.clickTrainParts[ii-1].len + shift
			currentReverbIndex = self.clickTrainParts[ii].reverbIndex + shift

			self.reverbs = numpy.append(self.reverbs, currentReverbIndex).astype(int)

	def get_predictions(self,positiveThreshold):

		for ii in range(0,self.numberParts):

			self.predictions.append(self.clickTrainParts[ii].prediction)
			self.clickPredictions = numpy.append(self.clickPredictions, self.clickTrainParts[ii].prediction * numpy.ones(self.clickTrainParts[ii].len))

			# Check if click train contains at least one positive part
			if self.positive == 0 and self.clickTrainParts[ii].prediction >= positiveThreshold:

				self.positive = 1

			# Count all positive parts of click train

			if self.clickTrainParts[ii].prediction >= positiveThreshold:

				self.numberPositiveParts += 1


class ClickTrainPart(object):

	def __init__(self,partNumber,clickTrainNumber,partData):

		# Basic parameters
		self.number = partNumber
		self.clickTrainNumber = clickTrainNumber
		self.data = partData
		self.time = partData[:,0]
		self.cd = partData[:,1].copy()
		self.ici = partData[:,2].copy()
		self.a130 = partData[:,3]
		self.a60 = partData[:,4]
		self.ratio = partData[:,3]/partData[:,4]

		#Misc parameters
		self.len = len(partData)

		if self.len < 4:

			self.shortLabel = 1

		else: 

			self.shortLabel = 0

class Preprocessing(object):

	def __init__(self):

		self.maxRatio = 3
		self.maxCD = 600
		self.maxICI = 0.149

	def truncate(self,clickTrainPart):

		clickTrainPart.ratio[(clickTrainPart.ratio >= self.maxRatio).nonzero()] = self.maxRatio
		clickTrainPart.cd[(clickTrainPart.cd >= self.maxCD).nonzero()] = self.maxCD
		clickTrainPart.ici[(clickTrainPart.ici >= self.maxICI).nonzero()] = self.maxICI

	def normalize(self,clickTrainPart):

		clickTrainPart.ratio = clickTrainPart.ratio/self.maxRatio
		clickTrainPart.cd = clickTrainPart.cd/self.maxCD
		clickTrainPart.ici = clickTrainPart.ici/self.maxICI

	def rescale(self,clickTrainPart):

		clickTrainPart.ratio = clickTrainPart.ratio*self.maxRatio
		clickTrainPart.cd = clickTrainPart.cd*self.maxCD
		clickTrainPart.ici = clickTrainPart.ici*self.maxICI

	def processForPrediction(clickTrainPart):

		#Parameters used for calculation
		clickTrainPart.medianCD = numpy.median(clickTrainPart.cd)

		if clickTrainPart.len-1 != 0:
			
			clickTrainPart.medianICI = numpy.median(clickTrainPart.ici[1:]) #FIX?

		else:

			clickTrainPart.medianICI = 0

		#Prediction parameters for clickTrain
		clickTrainPart.divCD = clickTrainPart.cd - clickTrainPart.medianCD
		clickTrainPart.divICI = numpy.append(0, clickTrainPart.ici[1:] - clickTrainPart.medianICI)
		clickTrainPart.diffCD = numpy.append(clickTrainPart.cd[0:-1]-clickTrainPart.cd[1:], 0)
		clickTrainPart.diffICI = numpy.append(clickTrainPart.ici[0:-1]-clickTrainPart.ici[1:], 0)
		clickTrainPart.cumsum = numpy.append(0, clickTrainPart.ici[1:]).cumsum(axis=0)

		# Find reverbs
		reverbThreshold = 0.65
		reverbDiv = (clickTrainPart.ici-clickTrainPart.medianICI)/clickTrainPart.medianICI
		clickTrainPart.reverbIndex = numpy.array((reverbDiv <= -reverbThreshold).nonzero())[0]

class Predict(object):

	def __init__(self,timeSteps,dataDim):

		self.timeSteps = timeSteps
		self.dataDim = dataDim

	def loadModel(self):

		# Load model and weights
		jsonFile = open('Model\model.json', 'r')
		loadedModelJson = jsonFile.read()
		jsonFile.close()
		self.loadedModel = model_from_json(loadedModelJson)
		self.loadedModel.load_weights("Model\model.h5")

	def prediction(self,clickTrainPart):

		#Prepare data for prediction
		dataToPredict = numpy.c_[clickTrainPart.cd,clickTrainPart.ici,clickTrainPart.a130,clickTrainPart.a60,
									clickTrainPart.ratio,clickTrainPart.cumsum, clickTrainPart.divICI,clickTrainPart.divCD,
										clickTrainPart.diffICI,clickTrainPart.diffCD]

		# Correct the input size & shape
		toPredict = numpy.zeros((self.timeSteps,self.dataDim))
		toPredict[:dataToPredict.shape[0],:dataToPredict.shape[1]] = dataToPredict
		toPredict = toPredict.ravel()
		reshapedForPrediction = toPredict.reshape(int(len(toPredict)/(self.timeSteps*self.dataDim)), self.timeSteps,self.dataDim)

		# Predict
		clickTrainPart.prediction = float(self.loadedModel.predict(reshapedForPrediction)[0])

def load_data(fileName):

	# Load dataset
	names = ['Time','Click Duration', 'Inter-Click Interval', 'Amplitude 130kHz Filter','Amplitude 60kHz Filter']
	inputDataArray = pandas.read_csv(fileName,names=names,skiprows=13)
	inputData = inputDataArray.values

	# Save start time
	timeInfo = pandas.read_csv(fileName,skiprows=8,nrows = 1)
	timeInfo = str(timeInfo.values[0][0])

	# Avoid dividing by zero
	zeroIndex = (inputData[:,4] == 0).nonzero()
	inputData[zeroIndex,4] = 0.0129

	return inputData, timeInfo

def extract_click_trains(inputData):

	# Set necessary parameters
	tmpClickTrain = numpy.array([])
	clickTrains = []
	clickTrainNumber = 1
	countedClicks = 0

	# Thresholds
	largestICI = 0.149
	lowestAmountClicks = 3

	# Extract click trains

	for k in range(0, inputData.shape[0]):

		# Begin    
		if inputData[k,2] > largestICI:

			if tmpClickTrain.shape[0] == 0:
				
				tmpClickTrain = inputData[k,]
				countedClicks += 1

			# Outside    
			else:

				if countedClicks > lowestAmountClicks:

					# Save extracted click train
					clickTrains.append(ClickTrain(clickTrainNumber,tmpClickTrain))

					# Iterate clickTrainNumber index
					clickTrainNumber += 1

				# Restart
				tmpClickTrain = numpy.array([])
				countedClicks = 0

		else:

			# Inside
			if tmpClickTrain.shape[0] != 0:

				tmpClickTrain = numpy.vstack((tmpClickTrain,inputData[k,]))
				countedClicks += 1

	return clickTrains

def preprocess_click_trains(clickTrains):

	preprocessingParameters = Preprocessing()

	for ll in range(0,len(clickTrains)):

		ClickTrain.split(clickTrains[ll],20)
		Preprocessing.truncate(preprocessingParameters,clickTrains[ll])
		Preprocessing.normalize(preprocessingParameters,clickTrains[ll])
		Preprocessing.rescale(preprocessingParameters,clickTrains[ll])

		for jj in range(0,clickTrains[ll].numberParts):
			
			Preprocessing.truncate(preprocessingParameters,clickTrains[ll].clickTrainParts[jj])
			Preprocessing.normalize(preprocessingParameters,clickTrains[ll].clickTrainParts[jj])
			Preprocessing.processForPrediction(clickTrains[ll].clickTrainParts[jj])

		ClickTrain.get_reverbs(clickTrains[ll])

	return clickTrains


def classify_click_trains(clickTrains,positiveThreshold):

	predictionParameters = Predict(20,10)
	Predict.loadModel(predictionParameters)

	for ll in range(0,len(clickTrains)):
		for jj in range(0,clickTrains[ll].numberParts):

			Predict.prediction(predictionParameters,clickTrains[ll].clickTrainParts[jj])

		ClickTrain.get_predictions(clickTrains[ll],positiveThreshold)


	return clickTrains