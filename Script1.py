# Michael M Bowser
# December 15, 2015
# Final Project
# This tool creates maps used in wetland delineation reports based on a project boundary supplied
# by the user. The tool navigates to two seperate drought monitoring websites and downloads three
# maps that are updated on a weekly basis. It also updates a series of other maps and text objects
# based information provided by the user. Once complete the tool prepares eight map documents and
# one final pdf that contain all eight maps.

import urllib
import arcpy, os
arcpy.env.overwriteOutput = True

# Workspace path - SHOULD BE ONLY PATH THAT NEEDS CHANGED
workspace = "M:/Arcgis/ToolBoxes/Scripts/FinalProject/"

# Set input parameters
palmerImage = arcpy.GetParameterAsText(0) # Prompts the user for a date of the Palmer Drought Map
usDroughtImage = arcpy.GetParameterAsText(1) # Prompts the user for a date of the U.S. Drought Map
outputLocation = arcpy.GetParameterAsText(2) # Prompts the user for a location to save the maps
inputShapefile = arcpy.GetParameterAsText(3) # Prompts the user for a shapefile for the project area
projectName = arcpy.GetParameterAsText(4) # Prompts the user for a project name
projectJobNumber = arcpy.GetParameterAsText(5) # Prompts the user for the project number
projectType = arcpy.GetParameterAsText(6) # Prompts the user for type of project (Site, Study Area, Project Area)

# Variables for USGS Map
indexHUC = workspace + "Data/MapMakerData.gdb/VA_HUC_12"
indexCOE = workspace + "Data/MapMakerData.gdb/COE_Subregions"

# Variables for FEMA Map
indexFEMA = workspace + "Data/MapMakerData.gdb/FEMA_Index_PWC"

# Get information about the input shapefile using the describe object properties
descObject = arcpy.Describe(inputShapefile) # Creates a describe object for the input shapefile
prjFilepath = descObject.path # Creates a variable that holds the file path for the input shapefile
prjBasename = descObject.basename # Creates a variable that holds the shapefile name

# Create a function to update the name, shapefile and spatial reference for each map
def updateMap (map):
    # Update project name text object with project name supplied by user
    for elm in arcpy.mapping.ListLayoutElements(map, "TEXT_ELEMENT" ,"projectName"):
        elm.text = projectName
    # Update legend text object with project type supplied by user
    for elm in arcpy.mapping.ListLayoutElements(map, "TEXT_ELEMENT" ,"legendName"):
        elm.text = projectType
    # Update project job number object with project number supplied by user
    for elm in arcpy.mapping.ListLayoutElements(map, "TEXT_ELEMENT" ,"projectNumber"):
        elm.text = "WSSI #" + projectJobNumber

    # Add shapefile supplied by user to map
    # Get the dataframes of the map
    df = arcpy.mapping.ListDataFrames(map)
    # Get layers in the first dataframe
    dfLayer = arcpy.mapping.ListLayers(map, "", df[0])
    # Loop through the layers in the dataframe list and replace data source
    for layer in dfLayer:
        revisedSite = dfLayer[0]
        revisedSite.replaceDataSource(prjFilepath, "SHAPEFILE_WORKSPACE", prjBasename)
    # Pan to input shapefile and update spatial reference
    sr = arcpy.Describe(revisedSite).spatialReference
    for dataframe in df:
        dataframe.spatialReference = sr

        dfPan = df[0]
        dfPan.panToExtent(revisedSite.getExtent())

  
# Palmer Drought Map

# Retrieve Palmer drought map and save on disk
urllib.urlretrieve("http://www.cpc.ncep.noaa.gov/products/analysis_monitoring/regional_monitoring/palmer/2015/" + palmerImage + ".gif", workspace + "Images/Palmer.jpg")
# Create variable containing Palmer drought map document
palmerMap = arcpy.mapping.MapDocument(workspace + "Maps/07_Palmer.mxd")
# Loop through layout elements to update picture element named tempImage
for elm in arcpy.mapping.ListLayoutElements(palmerMap, "PICTURE_ELEMENT", "*tempImage*"):
    if elm.name == "tempImage":
        elm.sourceImage = workspace + "Images/Palmer.jpg"
# Save Palmer Drought Map
palmerMap.saveACopy(outputLocation + "/07_Palmer.mxd")
del palmerMap

# US & Virginia Drought Maps

# Retrieve United States drought map and save on disk
urllib.urlretrieve("http://droughtmonitor.unl.edu/data/jpg/" + usDroughtImage +"/" + usDroughtImage +"_usdm.jpg", workspace + "Images/USDrought.jpg")
# Create variable containing US Drought map document
usDroughtMap = arcpy.mapping.MapDocument(workspace + "Maps/08_USDrought.mxd")
# Loop through layout elements to update picture element named usDrought
for elm in arcpy.mapping.ListLayoutElements(usDroughtMap, "PICTURE_ELEMENT", "*usDrought*"):
    if elm.name == "usDrought":
        elm.sourceImage = workspace + "Images/USDrought.jpg"
# Save US Drought Map
usDroughtMap.saveACopy(outputLocation + "/08_USDrought.mxd")
del usDroughtMap

# Retrieve Virginia drought map and save on disk
urllib.urlretrieve("http://droughtmonitor.unl.edu/data/jpg/" + usDroughtImage +"/" + usDroughtImage +"_va_text.jpg", workspace + "Images/VADrought.jpg")
# Create variable containing US Drought map document
vaDroughtMap = arcpy.mapping.MapDocument(workspace + "Maps/08_USDrought.mxd")
# Loop through layout elements to update picture element named usDrought
for elm in arcpy.mapping.ListLayoutElements(vaDroughtMap, "PICTURE_ELEMENT", "*vaDrought*"):
    if elm.name == "vaDrought":
        elm.sourceImage = workspace + "Images/VADrought.jpg"
# Save US Drought Map
vaDroughtMap.saveACopy(outputLocation + "/08_USDrought.mxd")
del vaDroughtMap


# Update all maps using the the update function
try:
# Location Map
    mapVicinity = arcpy.mapping.MapDocument(workspace + "Maps/01_Vicinity.mxd")
    updateMap(mapVicinity) # Update vicinity map using predefined function
    mapVicinity.saveACopy(outputLocation + "/01_Vicinity.mxd")
    del mapVicinity

# USGS Map
    mapUSGS = arcpy.mapping.MapDocument(workspace + "Maps/02_USGS.mxd")
    updateMap(mapUSGS) # Update USGS map using predefined function
    arcpy.AddField_management(inputShapefile, "latitude", "DOUBLE", "", "", "", "", "") # Add field to store latitude value
    arcpy.AddField_management(inputShapefile, "longitude", "DOUBLE", "", "", "", "", "") # Add field to store longitude value
    arcpy.CalculateField_management(inputShapefile, "latitude", "!SHAPE.CENTROID.X!", "PYTHON_9.3") # Calculate latitude value and store in new field
    arcpy.CalculateField_management(inputShapefile, "longitude", "!SHAPE.CENTROID.Y!", "PYTHON_9.3") # Calculate longitude value and store in new field

    # Use the search cursor to find lat and long fields   
    with arcpy.da.SearchCursor(inputShapefile, ("latitude", "longitude")) as cursor:
        for row in cursor:
            latValue = row[0] # Set the first row ("latitude") equal to the latValue variable
            longValue = row[1] # Set the second row ("longitude") equal to the longValue variable
        for elm in arcpy.mapping.ListLayoutElements(mapUSGS, "TEXT_ELEMENT", "coord"): # List text elements
            elm.text = "State Plane Coordinates" + '\n' + "N " + str(longValue) + " ft" + '\n' + "E " + str(latValue) + " ft" # Replace text element with coordinates

    # update map text to reflect hydrologic unit code (HUC) boundary
    dfList = arcpy.mapping.ListDataFrames(mapUSGS) # List dataframes in USGS map
    lyrList = arcpy.mapping.ListLayers(mapUSGS, "", dfList[0]) # List layers in dataframe
    projectArea = lyrList[0] # set the variable projectArea equal to the first layer in the list

    dfUSGS = dfList[0] # Set the variable dfUSGS equal to the first dataframe
    lyrListdfUSGS = arcpy.mapping.ListLayers(mapUSGS, "", dfUSGS) # List layers in the dfUSGS dataframe
    # Loop through layers in dataframe to find the HUC Index and use it to intersect the Project Area
    for lyrUSGS in lyrListdfUSGS: 
        indexHUC = lyrListdfUSGS[1]
        arcpy.SelectLayerByLocation_management(indexHUC, "INTERSECT", projectArea)

        # Use the search cursor to find the selected HUC Code and HUC Name        
        with arcpy.da.SearchCursor(indexHUC, ("HUC_12", "HU_12_NAME")) as cursor:
            for row in cursor:
                codeHUC = row[0]
                nameHUC = row[1]
            # Replace mxd text with new variables
            for elm in arcpy.mapping.ListLayoutElements(mapUSGS, "TEXT_ELEMENT", "huc"):
                elm.text = "Hydrologic Unit Code (HUC): " + codeHUC + "\n" + "Name of Watershed: " + nameHUC
            # Clear selection
            arcpy.SelectLayerByAttribute_management(indexHUC, "CLEAR_SELECTION")
    # Loop through layers in dataframe to find the COE Index and use it to intersect the Project Area
    for lyrUSGS in lyrListdfUSGS:
        indexCOE = lyrListdfUSGS[2]
        arcpy.SelectLayerByLocation_management(indexCOE, "INTERSECT", projectArea)
        # Use the search cursor to find the selected COE Region
        with arcpy.da.SearchCursor(indexCOE, ("COE_Region",)) as cursor:
            for row in cursor:
                regionCOE = row[0]
            for elm in arcpy.mapping.ListLayoutElements(mapUSGS, "TEXT_ELEMENT", "coe"):
                elm.text = "COE Region: " + regionCOE
            # Clear Selection
            arcpy.SelectLayerByAttribute_management(indexCOE, "CLEAR_SELECTION")            
            
    mapUSGS.saveACopy(outputLocation +  "/02_USGS.mxd") # Save as

    del mapUSGS, projectArea    
    

# NWI Map
    mapNWI = arcpy.mapping.MapDocument(workspace + "Maps/03_NWI_Digital.mxd")
    updateMap(mapNWI)
    mapNWI.saveACopy(outputLocation +  "/03_NWI_Digital.mxd")

    del mapNWI    

# Soils Map
    mapSoils = arcpy.mapping.MapDocument(workspace + "Maps/04_Soils_SSURGO.mxd")
    updateMap(mapSoils)
    mapSoils.saveACopy(outputLocation +  "/04_Soils_SSURGO.mxd")

    del mapSoils    

# FEMA Map
    mapFEMA = arcpy.mapping.MapDocument(workspace + "Maps/05_FEMA_DFirm.mxd")
    updateMap(mapFEMA)   

    # update map text to reflect FEMA Panel
    dfList = arcpy.mapping.ListDataFrames(mapFEMA) # List dataframes in USGS map
    lyrList = arcpy.mapping.ListLayers(mapFEMA, "", dfList[0]) # List layers in dataframe
    projectArea = lyrList[0] # set the variable projectArea equal to the first layer in the list

    dfFEMA = dfList[0] # Set the variable dfUSGS equal to the first dataframe
    lyrListdfFEMA = arcpy.mapping.ListLayers(mapFEMA, "", dfFEMA) # List layers in the dfUSGS dataframe
    # Loop through layers in dataframe to find the HUC Index and use it to intersect the Project Area
    for lyrFEMA in lyrListdfFEMA: 
        indexFEMA = lyrListdfFEMA[2]
        arcpy.SelectLayerByLocation_management(indexFEMA, "INTERSECT", projectArea)

        # Use the search cursor to find the selected HUC Code and HUC Name        
        with arcpy.da.SearchCursor(indexFEMA, ("FIRM_PAN", "EFF_DATE")) as cursor:
            for row in cursor:
                firmPanel = row[0]
                firmDate = row[1]
            # Replace mxd text with new variables
            for elm in arcpy.mapping.ListLayoutElements(mapFEMA, "TEXT_ELEMENT", "FEMApanel"):
                elm.text = "Panel " + firmPanel + " Effective " + str(firmDate)
            # Clear selection
            arcpy.SelectLayerByAttribute_management(indexFEMA, "CLEAR_SELECTION")

    mapFEMA.saveACopy(outputLocation +  "/05_FEMA_DFirm.mxd")        

    del mapFEMA    
   
# Aerial Map
    mapAerial = arcpy.mapping.MapDocument(workspace + "Maps/06_VBMP2013.mxd")
    updateMap(mapAerial)
    mapAerial.saveACopy(outputLocation +  "/06_VBMP2013.mxd")

    del mapAerial    

    # Create variables for the final map documents
    finalVicinity = arcpy.mapping.MapDocument(outputLocation + "/01_Vicinity.mxd")
    finalUSGS = arcpy.mapping.MapDocument(outputLocation + "/02_USGS.mxd")
    finalNWI = arcpy.mapping.MapDocument(outputLocation + "/03_NWI_Digital.mxd")
    finalSoils = arcpy.mapping.MapDocument(outputLocation + "/04_Soils_SSURGO.mxd")
    finalFEMA = arcpy.mapping.MapDocument(outputLocation + "/05_FEMA_DFirm.mxd")
    finalAerial = arcpy.mapping.MapDocument(outputLocation + "/06_VBMP2013.mxd")
    finalPalmer = arcpy.mapping.MapDocument(outputLocation + "/07_Palmer.mxd")
    finalDrought = arcpy.mapping.MapDocument(outputLocation + "/08_USDrought.mxd")

    # Export mxds to temporary individual pdfs
    deletePDFVicinity = arcpy.mapping.ExportToPDF(finalVicinity, outputLocation + "/del_Vicinity.PDF")
    deletePDFUSGS = arcpy.mapping.ExportToPDF(finalUSGS, outputLocation + "/del_USGS.PDF")
    deletePDFNWI = arcpy.mapping.ExportToPDF(finalNWI, outputLocation + "/del_NWI.PDF")
    deletePDFFEMA = arcpy.mapping.ExportToPDF(finalFEMA, outputLocation + "/del_FEMA.PDF")
    deletePDFSoils = arcpy.mapping.ExportToPDF(finalSoils, outputLocation + "/del_Soils.PDF")
    deletePDFAerial = arcpy.mapping.ExportToPDF(finalAerial, outputLocation + "/del_Aerial.PDF")
    deletePDFPalmer = arcpy.mapping.ExportToPDF(finalPalmer, outputLocation + "/del_Palmer.PDF")
    deletePDFDrought = arcpy.mapping.ExportToPDF(finalDrought, outputLocation + "/del_Drought.PDF")

    # Append individual pdfs into a single pdf
    appendPDF = arcpy.mapping.PDFDocumentCreate(outputLocation + "/Delin.pdf")
    appendPDF.appendPages(outputLocation + "/del_Vicinity.PDF")
    appendPDF.appendPages(outputLocation + "/del_USGS.PDF")
    appendPDF.appendPages(outputLocation + "/del_NWI.PDF")
    appendPDF.appendPages(outputLocation + "/del_FEMA.PDF")
    appendPDF.appendPages(outputLocation + "/del_Soils.PDF")
    appendPDF.appendPages(outputLocation + "/del_Aerial.PDF")
    appendPDF.appendPages(outputLocation + "/del_Palmer.PDF")
    appendPDF.appendPages(outputLocation + "/del_Drought.PDF")
    appendPDF.saveAndClose()

    del appendPDF, finalVicinity, finalUSGS, finalNWI, finalSoils, finalAerial, finalPalmer, finalDrought

    os.remove(str(outputLocation + "/del_Vicinity.PDF"))
    os.remove(str(outputLocation + "/del_USGS.PDF"))
    os.remove(str(outputLocation + "/del_NWI.PDF"))
    os.remove(str(outputLocation + "/del_FEMA.PDF"))
    os.remove(str(outputLocation + "/del_Soils.PDF"))
    os.remove(str(outputLocation + "/del_Aerial.PDF"))
    os.remove(str(outputLocation + "/del_Palmer.PDF"))
    os.remove(str(outputLocation + "/del_Drought.PDF"))
          
except:
    print arcpy.GetMessages()

