# Load libraries
import os
import numpy
import matplotlib
import matplotlib.pyplot as plt
import math
import wave
import array
import struct

#Load functions
import processClickTrains

class SoundGeneration(object):

	def __init__(self,fileName,method):

		# Basic parameters
		self.sin = math.sin
		self.twopi = 2*math.pi
		self.scalingCD = 10**-6
		self.freq130 = 130 * 10**3
		self.data = array.array('h')

		# File parameters
		self.fileName = fileName
		self.method = method

		# Misc
		porpoiseClickFrames = wave.open("Sound/porpoiseClick.wav", 'r').getnframes()
		bytePorpoiseClick = wave.open("Sound/porpoiseClick.wav", 'r').readframes(porpoiseClickFrames)
		self.porpoiseClick = struct.unpack("%ih" % porpoiseClickFrames, bytePorpoiseClick)
		self.porpoiseClick = self.porpoiseClick / numpy.amax(self.porpoiseClick)

	def get_click_train_data(self, clickTrain):

		self.cd = numpy.array(clickTrain.data[:,1])
		self.ici = numpy.append(clickTrain.ici[1:], 0.1)
		self.a130 = numpy.array(clickTrain.a130)
		self.a60 = numpy.array(clickTrain.a60)

	def get_sample_rate(self):

		if self.method == 2:

			self.sampleRate = int(48 * 10**3)

		else: 

			self.sampleRate = int(44.1 * 10**3)

	def get_parameters(self,currentIndex):

		if self.method == 1:

			self.freq1 = 2.03125 * 10**3
			self.freq2 = 0.9375 * 10**3
			self.volumeScale130 = 32767 * self.a130[currentIndex]/3.3
			self.volumeScale60 = 32767 * self.a60[currentIndex]/3.3
			self.cd[currentIndex] += (5/self.freq2) / self.scalingCD

		elif self.method == 2:

			if self.cd[currentIndex] < 75:

				self.cd[currentIndex] = 75

			self.freq1 = 1/(self.cd[currentIndex] * self.scalingCD)
			self.freq2 = 0
			self.volumeScale130 = 32767 * self.a130[currentIndex]/3.3
			self.volumeScale60 = 0

		elif self.method == 3:

			self.freq1 = 2.03125* 10**3
			self.freq2 = 0.9375* 10**3
			self.volumeScale130 = 32767 * self.a130[currentIndex]/3.3
			self.volumeScale60 = 32767 * self.a60[currentIndex]/3.3

			numberCycles130 = self.cd[currentIndex] * self.freq130
			self.cd[currentIndex] = numberCycles130 / self.freq1

	def get_silence(self,currentIndex):

		self.freq1 = 0
		self.freq2 = 0
		self.volumeScale130 = 0
		self.volumeScale60 = 0

	def save_file(self):
		
		soundFile = wave.open(self.fileName, 'w')
		soundFile.setparams((1, 2, self.sampleRate, 0, "NONE", "Uncompressed"))
		soundFile.writeframes(self.data.tostring())
		soundFile.close()

	def generate_audio_file_method_1to3(self):

		SoundGeneration.get_sample_rate(self)

		set_range = 2*len(self.cd)

		for soundPart in range(set_range):

			currentIndex = int(soundPart/2)

			if soundPart%2 == 0:

				SoundGeneration.get_parameters(self,currentIndex)
				numSamples = int(self.scalingCD * self.cd[currentIndex] * self.sampleRate)

			else:

				SoundGeneration.get_silence(self,currentIndex)
				numSamples = int(self.ici[currentIndex] * self.sampleRate)

			cyclesPerSample1 = float(self.freq1)/self.sampleRate
			cyclesPerSample2 = float(self.freq2)/self.sampleRate
			

			for samp in range(numSamples):

				phi = [samp * cyclesPerSample1, samp * cyclesPerSample2]
				phi[0] -= int(phi[0])
				phi[1] -= int(phi[1])

				sound = (self.volumeScale130 * self.sin(self.twopi * phi[0])) + (self.volumeScale60 * self.sin(self.twopi * phi[1]))

				self.data.append(int(round(sound)))

		SoundGeneration.save_file(self)

	def generate_audio_file_method_4(self):

		SoundGeneration.get_sample_rate(self)

		set_range = 2*len(self.cd)

		for soundPart in range(set_range):

			currentIndex = int(soundPart/2)
			numSamples = int(self.ici[currentIndex] * self.sampleRate)
			self.volumeScale130 = 32767 * self.a130[currentIndex]/3.3

			if soundPart%2 != 0:

				for samp in range(numSamples):

					self.data.append(int(round(0)))
			else:

				scaledPorpoiseClick = self.porpoiseClick * self.volumeScale130

				for samp in range(len(self.porpoiseClick)):
					
					self.data.append(int(round(scaledPorpoiseClick[samp])))

			SoundGeneration.save_file(self)

def generate_sounds(clickTrains,saveDir,onlyPositives,root,labelText,method):

	# Create path

	soundPathPos = saveDir + "\Sound files\Positive"

	if not os.path.exists(soundPathPos):
		os.makedirs(soundPathPos)

	# Check if only positives will be saved

	if onlyPositives == 1:

		posIndex = find_positive_click_trains(clickTrains)
		numberClickTrains = len(posIndex)
		clickTrainsToGenerate = numpy.array(clickTrains)[posIndex]

	else: 

		numberClickTrains = len(clickTrains)
		clickTrainsToGenerate = clickTrains

		soundPathNeg = saveDir + "\Sound files\\Negative"
		
		if not os.path.exists(soundPathNeg):
			os.makedirs(soundPathNeg)

	# Save sound files

	for k in range(0, numberClickTrains):

		# Check positive or negative

		clickTrainLabel = k + 1

		if clickTrainsToGenerate[k].positive == 1:

			if onlyPositives == 1:
				
				clickTrainLabel = posIndex[k] + 1

			fileName = soundPathPos + "\Click train %05d.wav" %clickTrainLabel

		else: 

			fileName = soundPathNeg + "\Click train %05d.wav" %clickTrainLabel

		# Set necessary parameters

		soundToSave = SoundGeneration(fileName, method)
		SoundGeneration.get_click_train_data(soundToSave,clickTrainsToGenerate[k])
		SoundGeneration.get_sample_rate(soundToSave)

		if method != 4:

			SoundGeneration.generate_audio_file_method_1to3(soundToSave)

		else:

			SoundGeneration.generate_audio_file_method_4(soundToSave)

		progress = 'Saving click train sound %d out of %d' %(k+1,numberClickTrains)
		labelText.set(progress)
		root.update()

def find_positive_click_trains(clickTrains):

	# Find all positive click trains

	posIndex = []

	for ll in range(0,len(clickTrains)):
		
		if clickTrains[ll].positive == 1:

			posIndex.append(ll)

	return posIndex


def plot_predictions(clickTrains,timeInfo,saveDir,onlyPositives,root,labelText):

	# Fixed figure settings for all figures
	fig1 = plt.figure()

	ax0 = fig1.add_subplot(4, 1, 1)
	ax0.set_title('Inter-Click Interval')
	plt.xlabel('Time [s]')
	plt.ylabel('Time [ms]')

	ax1 = fig1.add_subplot(4, 1, 2)
	ax1.set_title('Click Duration')
	plt.xlabel('Time [s]')
	plt.ylabel('Time [µs]')

	ax2 = fig1.add_subplot(4, 1, 3)
	ax2.set_title('Amplitude Ratio')
	plt.xlabel('Time [s]')
	plt.ylabel('Ratio 130kHz to 60kHz')

	ax5 = fig1.add_subplot(4, 1, 4)
	ax5.set_title('Prediction')
	plt.xlabel('Click Train Number')
	plt.ylabel('Likelihood')

	fScoreTresholds = [0.8512709140777588,0.5718547701835632,0.4109937250614166]

	ax5.axhline(y=fScoreTresholds[0], color='g', linestyle='--')
	ax5.axhline(y=fScoreTresholds[1], color='k', linestyle='--')
	ax5.axhline(y=fScoreTresholds[2], color='r', linestyle='--')

	figure1 = plt.gcf()
	figure1.set_size_inches(15, 10)
	fig1.tight_layout()

	# Fixed figure settings
	fig2 = plt.figure()
	ax20 = fig2.add_subplot(4, 1, 1)
	ax20.set_title('Inter-Click Interval')
	plt.xlabel('Time [s]')
	plt.ylabel('Time [ms]')

	ax21 = fig2.add_subplot(4, 1, 2)
	ax21.set_title('Amplitude 130kHz Filter')
	plt.xlabel('Time [s]')
	plt.ylabel('Amplitude [V]')

	ax22 = fig2.add_subplot(4, 1, 3)
	ax22.set_title('Amplitude 60kHz Filter')
	plt.xlabel('Time [s]')
	plt.ylabel('Amplitude [V]')

	ax25 = fig2.add_subplot(4, 1, 4)
	ax25.set_title('Prediction')
	plt.xlabel('Click Train Number')
	plt.ylabel('Likelihood')

	ax25.axhline(y=fScoreTresholds[0], color='g', linestyle='--')
	ax25.axhline(y=fScoreTresholds[1], color='k', linestyle='--')
	ax25.axhline(y=fScoreTresholds[2], color='r', linestyle='--')

	figure2 = plt.gcf()
	figure2.set_size_inches(15, 10)
	fig2.tight_layout()


	# Create dir
	posPath = saveDir + '\Plots\Click trains\\Positive'

	if not os.path.exists(posPath):
		os.makedirs(posPath)

	# Check if only positives will be saved

	if onlyPositives == 1:

		posIndex = find_positive_click_trains(clickTrains)
		numberClickTrains = len(posIndex)
		clickTrainsToPlot = numpy.array(clickTrains)[posIndex]

	else: 

		numberClickTrains = len(clickTrains)
		clickTrainsToPlot = clickTrains

		negPath = saveDir + '\Plots\Click trains\\Negative'
		
		if not os.path.exists(negPath):
			os.makedirs(negPath)

	color1 = 'm'
	color2 = 'b'
	color3 = 'y'
	color4 = 'c'
	color5 = 'k'
	color6 = 'g'

	rescaleICI = 1000

	# Save images

	for k in range(0, numberClickTrains):
			
		indexReverb = clickTrainsToPlot[k].reverbs
		indexNoReverb = numpy.delete(numpy.arange(0,clickTrainsToPlot[k].len),indexReverb)
		seperationIndex = numpy.arange(0,clickTrainsToPlot[k].len,20)
		time = clickTrainsToPlot[k].time - clickTrainsToPlot[k].time[0]


		timeStamp = "Time elapsed: " + str(clickTrainsToPlot[k].time[0]) +  " s"
		#an0 = ax0.text(0.5, 0.5, timeStamp, size=24, ha='center', va='center')
		#an1 = ax20.annotate(timeStamp, (0.05, 1.05), textcoords='axes fraction', size=15)

		plt.figure(fig1.number)
		an00 = plt.figtext(0.05, 0.975, timeStamp, color='black', weight='roman',
	            size=12)
		plt.figure(fig2.number)
		an10 = plt.figtext(0.05, 0.975, timeStamp, color='black', weight='roman',
	            size=12)

		plt.figure(fig1.number)
		an01 = plt.figtext(0.705, 0.975, timeInfo, color='black', weight='roman',
	            size=12)
		plt.figure(fig2.number)
		an11 = plt.figtext(0.705, 0.975, timeInfo, color='black', weight='roman',
	            size=12)

		for m in range(1,len(seperationIndex)):

			currentIndex = seperationIndex[m]-1
			avline0 = ax0.axvline(x=time[currentIndex], color='k', linestyle='--')
			avline1 = ax1.axvline(x=time[currentIndex], color='k', linestyle='--')
			avline2 = ax2.axvline(x=time[currentIndex], color='k', linestyle='--')

			avline20 = ax20.axvline(x=time[currentIndex], color='k', linestyle='--')
			avline21 = ax21.axvline(x=time[currentIndex], color='k', linestyle='--')
			avline22 = ax22.axvline(x=time[currentIndex], color='k', linestyle='--')

		timeNoReverb = time[indexNoReverb]
		timeReverb = time[indexReverb]
		xmax = numpy.amax(time,axis=0)

		if timeNoReverb.shape[0] != 0:

			ax00 = ax0.stem(timeNoReverb,clickTrainsToPlot[k].ici[indexNoReverb]*rescaleICI, color1)
			ax01 = ax1.stem(timeNoReverb,clickTrainsToPlot[k].cd[indexNoReverb], color2)
			ax02 = ax2.stem(timeNoReverb,clickTrainsToPlot[k].ratio[indexNoReverb], color3)

			ax020 = ax20.stem(timeNoReverb,clickTrainsToPlot[k].ici[indexNoReverb]*rescaleICI, color1)
			ax021 = ax21.stem(timeNoReverb,clickTrainsToPlot[k].a130[indexNoReverb], color4)
			ax022 = ax22.stem(timeNoReverb,clickTrainsToPlot[k].a60[indexNoReverb], color5)


		if timeReverb.shape[0] != 0:


			ax10 = ax0.stem(timeReverb,clickTrainsToPlot[k].ici[indexReverb]*rescaleICI, color6)
			ax11 = ax1.stem(timeReverb,clickTrainsToPlot[k].cd[indexReverb], color6)
			ax12 = ax2.stem(timeReverb,clickTrainsToPlot[k].ratio[indexReverb], color6)

			ax120 = ax20.stem(timeReverb,clickTrainsToPlot[k].ici[indexReverb]*rescaleICI, color6)
			ax121 = ax21.stem(timeReverb,clickTrainsToPlot[k].a130[indexReverb], color6)
			ax122 = ax22.stem(timeReverb,clickTrainsToPlot[k].a60[indexReverb], color6)

		lim0 = ax0.axis([ -0.001, 1.3*xmax, 0, 149*1.1])
		lim1 = ax1.axis([ -0.001, 1.3*xmax, 0, 600*1.1])
		lim2 = ax2.axis([ -0.001, 1.3*xmax, 0, 3*1.1])

		lim20 = ax20.axis([ -0.001, 1.3*xmax, 0, 149*1.1])
		lim21 = ax21.axis([ -0.001, 1.3*xmax, 0, 3.3])
		lim22 = ax22.axis([ -0.001, 1.3*xmax, 0, 3.3])

		currentPrediction = clickTrainsToPlot[k].predictions

		ax05 = ax5.stem(numpy.arange(0,len(currentPrediction), dtype=int), currentPrediction, 'r', zorder=1)
		lim5 = ax5.set_ylim([0,1])
		lim5 = ax5.set_xlim([-0.1,len(currentPrediction)-1+0.1])

		ax225 = ax25.stem(numpy.arange(0,len(currentPrediction), dtype=int), currentPrediction, 'r', zorder=1)
		lim25 = ax25.set_ylim([0,1])
		lim25 = ax25.set_xlim([-0.1,len(currentPrediction)-1+0.1])

		clickTrainLabel = k + 1

		if clickTrainsToPlot[k].positive == 1:

			if onlyPositives == 1:

				clickTrainLabel = posIndex[k] + 1

			image_dir1 = saveDir + '\Plots\\Click trains\\Positive\Click train %05d 1' %clickTrainLabel
			image_dir2 = saveDir + '\Plots\\Click trains\\Positive\Click train %05d 2' %clickTrainLabel

		else:

			image_dir1 = saveDir + '\Plots\\Click trains\\Negative\Click train %05d 1' %clickTrainLabel
			image_dir2 = saveDir + '\Plots\\Click trains\\Negative\Click train %05d 2' %clickTrainLabel

		fig1.savefig(image_dir1,dpi = 100)    # save the figure to file
		fig2.savefig(image_dir2,dpi = 100)    # save the figure to file
		progress = 'Saving click train %d out of %d' %(k+1,numberClickTrains)
		labelText.set(progress)
		root.update()

		if timeNoReverb.shape[0] != 0:

			ax00.remove()
			ax01.remove()
			ax02.remove()

			ax020.remove()
			ax021.remove()
			ax022.remove()

		if timeReverb.shape[0] != 0:

			ax10.remove()
			ax11.remove()
			ax12.remove()

			ax120.remove()
			ax121.remove()
			ax122.remove()

		for m in range(1,len(seperationIndex)):

			ax0.lines[0].remove()
			ax1.lines[0].remove()
			ax2.lines[0].remove()

			ax20.lines[0].remove()
			ax21.lines[0].remove()
			ax22.lines[0].remove()

		ax05.remove()
		ax225.remove()

		an00.remove()
		an10.remove()
		an01.remove()
		an11.remove()

		lim0.remove(0)
		lim1.remove(0)
		lim2.remove(0)

		lim20.remove(0)
		lim21.remove(0)
		lim22.remove(0)

def count_unique_numbers(inputArray):

	maxVal = int(numpy.amax(inputArray))
	arrayLength = len(inputArray)
	countingArray = numpy.array([])
	hourArray = numpy.array([])
	start = 0

	for ii in range(0,maxVal):

		hourArray = numpy.append(hourArray, ii)

		counter = len((inputArray == ii).nonzero()[0])

		countingArray = numpy.append(countingArray, counter)


	return hourArray, countingArray

def plot_axvline(inputArray, seperation):

	inpArrLen = len(inputArray)
	seperationIndex = numpy.arange(0,inpArrLen,seperation)
	sepIndLen = len(seperationIndex)

	for k in range(0,sepIndLen):

		currentIndex = seperationIndex[k]
		plt.axvline(x=inputArray[currentIndex], color='k', linestyle='--')


def positive_minutes_per_hour(positiveMinutes, positiveMinutesCounter):
	
	posMinLen = len(positiveMinutes)
	positiveMinuteHours = numpy.floor(positiveMinutes/60)
	maxHour = int(numpy.amax(positiveMinuteHours))
	positiveMinutesperHour = numpy.array([])
	hourArray = numpy.arange(0,maxHour)

	for m in range(0,maxHour):

		currentHourIndex = (positiveMinuteHours == m).nonzero()
		currentHourCounter = positiveMinutesCounter[currentHourIndex]

		for l in range(0,len(currentHourCounter)):

			if currentHourCounter[l] >= 1:

				currentHourCounter[l] = 1

		positiveMinutesperHour = numpy.append(positiveMinutesperHour, numpy.sum(currentHourCounter))

	return positiveMinutesperHour,hourArray

def plot_general_results(clickTrains, timeInfo, saveDir):

	# Get all times for positive clicks and remove reverbs

	allPositivesTimes = numpy.array([])

	for ll in range(0,len(clickTrains)):

		if clickTrains[ll].positive == 1:

			noReverbTimes = numpy.delete(clickTrains[ll].time, clickTrains[ll].reverbs)
			allPositivesTimes = numpy.append(allPositivesTimes, noReverbTimes)			

	# Calculate number of positive clicks per hour

	allPositivesHours = numpy.floor(allPositivesTimes/(60*60))
	allPostivesMinutes = numpy.floor(allPositivesTimes/60)

	positiveHours, positiveHoursCounter = count_unique_numbers(allPositivesHours)
	positiveMinutes, positiveMinutesCounter = count_unique_numbers(allPostivesMinutes)

	# Positive minutes per hour

	positiveMinutesperHour,hourArray = positive_minutes_per_hour(positiveMinutes, positiveMinutesCounter)

	# Create directory

	genPath = saveDir + '\Plots\General results' 

	if not os.path.exists(genPath):
		os.makedirs(genPath)

	image_dir1 = saveDir + '\Plots\\General results\Plot Positive min per hour'
	image_dir2 = saveDir + '\Plots\\General results\Plot Porpoise clicks per hour'

	plt.clf()
	plt.cla()
	plt.figtext(0.505, 0.975, timeInfo, color='black', weight='roman',
	            size=7)
	width = 1/1.5
	plt.bar(hourArray.astype(int), positiveMinutesperHour.astype(int), width, color="c")
	plot_axvline(hourArray, 12)
	plt.xlabel('Time in hours')
	plt.ylabel('Positive minutes')
	plt.ylim((0,60))
	plt.title('Positive minutes per hour')
	plt.savefig(image_dir1,dpi = 150)

	plt.cla()
	plt.figtext(0.505, 0.975, timeInfo, color='black', weight='roman',
	            size=7)

	width = 1/1.5
	plt.bar(positiveHours.astype(int), positiveHoursCounter.astype(int), width, color="g")
	plot_axvline(positiveHours, 12)
	plt.xlabel('Time in hours')
	plt.ylabel('Number of porpoise clicks')
	plt.ylim((0,400))
	plt.title('Porpoise clicks per hour')
	plt.savefig(image_dir2,dpi = 150)

def save_txt_file(clickTrains, saveDir, classLevel):
	
	# Calculate parameters to save	
	totalNumberPositiveParts = 0
	totalNumberParts = 0

	for ll in range(0,len(clickTrains)):

		totalNumberPositiveParts += clickTrains[ll].numberPositiveParts
		totalNumberParts += clickTrains[ll].numberParts

	# Other parameters to save

	posIndex = find_positive_click_trains(clickTrains)
	totalNumberPositiveClickTrains = len(posIndex)
	totalNumberClickTrains = len(clickTrains)

	# Set path

	dataPath = saveDir + '\Data files' 

	if not os.path.exists(dataPath):
		os.makedirs(dataPath)

    # Save txt file

	clickTrainData = ("\nNumber of click train parts extracted: " + str(totalNumberParts) + 
				      "\nNumber of positively classified click train parts: " + str(totalNumberPositiveParts) + classLevel +
				      "\nNumber of click trains extracted: " + str(totalNumberClickTrains) +
				      "\nNumber of click trains with at least one positively classified click train part: " + str(totalNumberPositiveClickTrains)
				      )

	text_file = open(dataPath + "/Click Train Data.txt", "w")
	text_file.write(clickTrainData)
	text_file.close()


def save_csv_files(clickTrains, saveDir, filesToSave):


	#Initial parameters
	preprocessingParameters = processClickTrains.Preprocessing()
	allClickTrainWithPredictions = numpy.array([], dtype=numpy.int64).reshape(0,6)
	positiveClickTrains = numpy.array([], dtype=numpy.int64).reshape(0,5)


	for ll in range(0,len(clickTrains)):

			tmpData = numpy.c_[clickTrains[ll].data, clickTrains[ll].clickPredictions]
			allClickTrainWithPredictions = numpy.vstack((allClickTrainWithPredictions, tmpData))

			if clickTrains[ll].positive == 1:

				tmpData = numpy.delete(clickTrains[ll].data,clickTrains[ll].reverbs,axis=0)
				positiveClickTrains = numpy.vstack((positiveClickTrains, tmpData))

	allClickTrainWithoutPredictions = allClickTrainWithPredictions[:,[0,1,2,3,4]]

	dataPath = saveDir + '/Data files' 

	if not os.path.exists(dataPath):
		os.makedirs(dataPath)

	if filesToSave == 1 or filesToSave == 4:

		numpy.savetxt(dataPath + "/Positively classified click trains.csv", positiveClickTrains, delimiter=",",fmt='%.8f')

	if filesToSave == 2 or filesToSave == 4:

		numpy.savetxt(dataPath + "/All click trains without probabilities.csv", allClickTrainWithoutPredictions, delimiter=",",fmt='%.8f')
	
	if filesToSave == 3 or filesToSave == 4:
	
		numpy.savetxt(dataPath + "/All click trains with probabilities.csv", allClickTrainWithPredictions, delimiter=",",fmt='%.8f')