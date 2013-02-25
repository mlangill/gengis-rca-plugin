import GenGIS

import rpy2
import rpy2.robjects as robjects
r = robjects.r

import os

#Uncomment this to allow run-time debugging
#import pdb; pdb.set_trace()

# define path to this plugin with the R environment
pluginPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),'')

print pluginPath
robjects.globalEnv["hDir"] = pluginPath

'''
Example usage:
sys.path.append("C:\\Projects\\B2.0\\Armanini-CABIN\\Fredericton-RCA\\")
from CABIN_RCA import *
RCA_Example = CABIN_RCA("Group","Label","Count")
RCA_Example.Run_RCA("OoverE")
'''

##################################################;
# R code to build a Rivpacs-type model for Atlantic Canada as per Armanini et al. (Submitted);
# The code here presented is a simplified version with respect to the one used to develop and test the RCA model; It is design to quickly input and test new test dataset
# set up 12 September 2011, for Atlantic Canada data;
# For R versions >= 2.11.1;
# Please cite: Armanini D.G., Monk W.A., Carter L., Cote D. & Baird D.J. Submitted. A biomonitoring Reference Condition Model for rivers in Atlantic Canada. 
##################################################;
# ACKNOWLEDGMENTS
#
# We would like to acknowledge partners who have made this paper possible by sharing their data: 
# 1) the New Brunswick Department of Environment (New Brunswick DENV); 
# 2) Defense Canada, Base Gagetown; 
# 3) Environment Canada's National Agri-Environmental Standards Initiative (NAESI); 
# 4) Canadian Rivers Institute (CRI); and 
# 5) the Canadian Aquatic Biomonitoring Network (CABIN) network; 6) Parks Canada. 
#
# We would also like to thank Dr. John Van Sickle (USEPA) for generously sharing R scripts and for reviewing an earlier version of the manuscript 
# and Pierre Martel (Parks Canada) for support on the Upper Mersey dataset. 
# This research was supported through program funding from Environment Canada.
##################################################;

class CABIN_RCA:

	### Initialize the data structure. setCol is the name of the group column (e.g., 'cal','val','test'), spCol is the name of the column in the sequence file that has diversity data, and countCol is the column that has count information.
	def __init__(self, setCol, spCol, countCol):
		self.setLabel = setCol
		self.speciesLabel = spCol
		self.countField = countCol
		
		self.graphicalElementIds = []

	def create_rca_model(self):
		'''Creates a RCA model'''
		#1)Get "cal" data
		#2)process and create RCA model
		#3)Save model to disk
		pass

	### Run the reference condition analysis. Since this was initially written as an R script, most of the R code is simply preserved intact, with RPy used to pass data into and out of the original script. ###		
	def Run_RCA(self,colToPlot = None):
		'''Runs test data against the given RCA model'''

		### Get the layer data ###
		locs = GenGIS.layerTree.GetLocationSetLayer(0).GetAllActiveLocationLayers()
		testLocs = []
		
		### Get the label types ###
		labelsToCreate = set()
		for locX in locs:
			labelsToCreate.add(locX.GetController().GetData()[self.setLabel])
		
		#################################### ENVIRONMENTAL DATA #####################################
		envFields = ["geo_sed", "geo_intr", "geo_sedvol", "clim_Trange"]
		
		### Hash of hashes to store the env field data
		envValues = {}
		for lab in labelsToCreate:
			envValues[lab] = {}
			
		### Iterate through the environmental data and build dictionary of values
		for loc in locs:
		
			### Create the entry for this location
			locType = loc.GetController().GetData()[self.setLabel]
			if locType == "test":
				testLocs.append(loc)
			
			siteID = loc.GetController().GetData()["Site ID"]
			envValues[locType][siteID] = {}
			
			### Add values for each environmental value
			for envField in envFields:
				data = loc.GetController().GetData()[envField]
				envValues[locType][siteID][envField] = data
				
		### Build habitat data frame for each subset of samples
		for labDo in labelsToCreate:
			
			### The list of names ###
			PyNameList = envValues[labDo].keys()
			numExamples = len(PyNameList)
			
			RnameList = r["c"](robjects.StrVector(PyNameList))
			RenvList = r["c"](robjects.StrVector(envFields))
			Rdims = r["list"](RnameList,RenvList)
			
			RvarName = str(labDo + "_HAB_NAME")
			robjects.globalEnv[RvarName] = RnameList
			
			### The habitat value matrix ###
			PyHabList = []
			for addName in PyNameList:
				for addEnv in envFields:
					if addEnv in envValues[labDo][addName].keys():
						PyHabList.append(float(envValues[labDo][addName][addEnv]))
					else:
						PyHabList.append(0.0)
			
			### Create the matrix and send it to R ###
			RhabList = r["c"](robjects.FloatVector(PyHabList))
			RhabMatrix = r.matrix(RhabList, nrow = numExamples, byrow = True, dimnames = Rdims)
			RhabName = str(labDo + "_HAB_MATR")
			robjects.globalEnv[RhabName] = RhabMatrix
			
			### Create the data frame in R ###
			RhabFrName = str(labDo + "_HAB_FRAME")
			r(RhabFrName + " = data.frame(" + RhabName + ")")
		
		###################################### SEQUENCE DATA ########################################
		
		### Get the species names for indexing
		speciesList = set()
		for seqLayer in GenGIS.layerTree.GetSequenceLayers():
			seqController = seqLayer.GetController()
			if seqController.IsActive():
				speciesList.add(seqController.GetData()[self.speciesLabel])
		
		### Hash of hashes to store the species count data
		speciesCounts = {}
		for lab in labelsToCreate:
			speciesCounts[lab] = {}
			
		### Iterate through the sequence data and build the dictionary of counts
		for loc in locs:
			
			### Create the entry for this location
			locType = loc.GetController().GetData()[self.setLabel]
			siteID = loc.GetController().GetData()["Site ID"]
			speciesCounts[locType][siteID] = {}
			
			### Add values for each observed species
			seqLayers = loc.GetAllActiveSequenceLayers()
			for seqLayer in seqLayers:
				data = seqLayer.GetController().GetData()
				speciesCounts[locType][siteID][data[self.speciesLabel]] = data[self.countField]
		
		### Build species data frame for each subset of samples
		for labDo in labelsToCreate:
			
			### The list of names ###
			PyNameList = speciesCounts[labDo].keys()
			numExamples = len(PyNameList)
			
			RnameList = r["c"](robjects.StrVector(PyNameList))
			RspList = r["c"](robjects.StrVector(list(speciesList)))
			Rdims = r["list"](RnameList,RspList)
			
			RvarName = str(labDo + "_SP_NAME")
			robjects.globalEnv[RvarName] = RnameList
			
			### The biodiversity matrix ###
			PyDivList = []
			for addName in PyNameList:
				for addSpecies in speciesList:
					if addSpecies in speciesCounts[labDo][addName].keys():
						PyDivList.append(float(speciesCounts[labDo][addName][addSpecies]))
					else:
						PyDivList.append(0.0)
			
			### Create the matrix and send it to R ###
			RdivList = r["c"](robjects.FloatVector(PyDivList))
			RdivMatrix = r.matrix(RdivList, nrow = numExamples, byrow = True, dimnames = Rdims)
			RmatName = str(labDo + "_SP_MATR")
			robjects.globalEnv[RmatName] = RdivMatrix
			
			### Create the data frame in R ###
			RfrName = str(labDo + "_SP_FRAME")
			r(RfrName + " = data.frame(" + RmatName + ")")

		############################################ RCA R CODE ################################################
			
		r('''
                #location of R library
		infile <- paste(hDir,"rca_functions.r",sep="")
		source(infile)

                #location of RCA model
                model<-paste(hDir,"atlantic_rca_model.RData",sep="")

                #names of output files to write results to
		outfile <- paste(hDir,"OE_test_GG.csv",sep="")
                outfile_ra <- paste(hDir,"OE_test_GG_ra.csv",sep="")

                rca_results<-run_test_rca(test_HAB_FRAME,test_SP_FRAME,outfile,outfile_ra,model)

                ''')

		if colToPlot:
			toPlot = list(r("rca_results$OE.assess.test$OE.scores$" + colToPlot))
			self.ViewportPlot(toPlot,testLocs)
			
	def clearLines(self):
		for id in self.graphicalElementIds:
			GenGIS.graphics.RemoveLine(id)
		GenGIS.viewport.Refresh()
		
	def ViewportPlot(self,data,locations):

		print "Running ViewportPlot..."
		terrainController = GenGIS.layerTree.GetMapLayer(0).GetController()
		
		# desired plot attributes
		lineWidth = 5
		userScaleFactor = 0.2
							
		maxValue = max(max(data), abs(min(data)))
		if maxValue != 0:
			scaleFactor = (0.2 * terrainController.GetWidth()) / maxValue
		else:
			scaleFactor = 0
		scaleFactor *= userScaleFactor

		# get min and max values for mapping colours
		if min(data) < 0 and max(data) > 0:
			# have both negative and positive values so map negative values to 
			# first half of map and positive values to the second half of the map
			maxValue = max(max(data), -min(data))
			minValue = -maxValue
		else:
			# all data is either negative or positive so just map over the full colour map
			#minValue = min(data)
			#maxValue = max(data)
			minValue = 0.0
			maxValue = 1.0

		# plot data
		self.graphicalElementIds = []
		for i in xrange(0, len(locations)):
			locLayer = locations[i]
			geoCoord = GenGIS.GeoCoord(locLayer.GetController().GetLongitude(), locLayer.GetController().GetLatitude())
			pos = GenGIS.Point3D()
			terrainController.GeoToGrid(geoCoord, pos)

			colourMap = GenGIS.colourMapManager.GetColourMap('Diverging (Red-White)')
			print str(i) + "   " + str(data[i])
			colour = colourMap.GetInterpolatedColour(min(data[i],1.0), minValue, maxValue)
			
			endPos = GenGIS.Point3D(pos.x, scaleFactor * abs(data[i]), pos.z)
			line = GenGIS.VisualLine(colour, lineWidth, GenGIS.LINE_STYLE.SOLID, GenGIS.Line3D(pos, endPos))
			lineId = GenGIS.graphics.AddLine(line)
			self.graphicalElementIds.append(lineId)
		
		GenGIS.viewport.Refresh()
