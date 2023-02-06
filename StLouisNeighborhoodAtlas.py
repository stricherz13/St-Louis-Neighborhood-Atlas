# Created by: Brad Stricherz
# Created on: October 15th, 2022
# This script will create a pdf map book of every neighborhood in St Louis.

# import modules
import arcpy
import os
from datetime import date

# Workspace and environmental variables
arcpy.env.overwriteOutput = True
arcpy.env.workspace = arcpy.GetParameterAsText(0)

# Parameters for the geoprocessiong tool
layoutName = arcpy.GetParameterAsText(1)
mapFrameName = arcpy.GetParameterAsText(2)
indexLyrName = arcpy.GetParameterAsText(3)
indexFieldName = arcpy.GetParameterAsText(4)
coverPDF = arcpy.GetParameterAsText(5)
outputFolderPath = arcpy.GetParameterAsText(6)
pdfFileName = arcpy.GetParameterAsText(7)

# arcpy.mp objects for the map book creation.
project = arcpy.mp.ArcGISProject("current")
layout = project.listLayouts(layoutName)[0]
mainMF = layout.listElements("mapframe_element", mapFrameName)[0]
indexLyr = mainMF.map.listLayers(indexLyrName)[0]

# counters for the loop and page numbers
pageNum = 1
count = 0
# parsing the attribute fields to create a list for the loop.
nhd_list = []
with arcpy.da.SearchCursor(indexLyrName, indexFieldName) as cursor:
    for row in cursor:
        nhd_list.append(row)

neighborhood = sorted(nhd_list)
neighborhoodOut = [item for i in neighborhood for item in i]
pageNameList = neighborhoodOut

# script begins to loop through each neighborhood to create individual maps.
for pageName in pageNameList:
    print(pageName)
    arcpy.AddMessage("Processing page: " + pageName)

    # This if/else statement SearchCursor is used to loop through the neighborhood names list that was created
    # above.
    field = arcpy.ListFields(indexLyr.dataSource, indexFieldName)[0]
    if field.type == "String":
        pageIndexCursor = arcpy.SearchCursor(indexLyr.dataSource, indexFieldName + " = '" + pageName + "'")
    else:
        pageIndexCursor = arcpy.SearchCursor(indexLyr.dataSource, indexFieldName + " = " + pageName)

    pageIndexRow = pageIndexCursor.next()

    # Camera sets the extent of the main map frame to each neighborhood extent.
    mainMF.camera.setExtent(pageIndexRow.Shape.extent)

    # these lines of code create the indicator map that is the lower right corner of each map.
    locMF = layout.listElements("mapframe_element", "Locator Map Frame")[0]
    locExt = locMF.camera.getExtent()
    mainExt = mainMF.camera.getExtent()
    locRec = layout.listElements("graphic_element", "Rectangle 1")[0]
    locRec.elementPositionX = locMF.elementPositionX + (
            ((mainExt.XMin - locExt.XMin) / (locExt.XMax - locExt.XMin)) * locMF.elementWidth)
    locRec.elementPositionY = locMF.elementPositionY + (
            ((mainExt.YMin - locExt.YMin) / (locExt.YMax - locExt.YMin)) * locMF.elementHeight)
    locRec.elementWidth = (((mainExt.XMax - mainExt.XMin) / (locExt.XMax - locExt.XMin)) * locMF.elementWidth)
    locRec.elementHeight = (((mainExt.YMax - mainExt.YMin) / (locExt.YMax - locExt.YMin)) * locMF.elementHeight)

    # This for loop updates the text on the layout to include the title, year, and page number.
    for field in arcpy.ListFields(indexLyr.dataSource):
        print(field)
        for dynTxt in layout.listElements("text_element"):
            print(dynTxt)
            if dynTxt.name == field.name:
                dynTxt.text = pageIndexRow.getValue(field.name)
            elif dynTxt.name == "Year":
                dynTxt.text = date.today().year
            elif dynTxt.name == "PageNum":
                dynTxt.text = pageNum

    # the scipt below creates the PDF file for the map book. Count is used to skip these lines if a map book has
    # already been created.
    if count == 0:
        if os.path.exists(os.path.join(outputFolderPath, pdfFileName)):
            os.remove(os.path.join(outputFolderPath, pdfFileName))
        pdfDoc = arcpy.mp.PDFDocumentCreate(os.path.join(outputFolderPath, pdfFileName))
        pdfDoc.appendPages(coverPDF)

    layout.exportToPDF(os.path.join(outputFolderPath, "Temp_" + str(count) + ".pdf"))
    pdfDoc.appendPages(os.path.join(outputFolderPath, "Temp_" + str(count) + ".pdf"))
    os.remove(os.path.join(outputFolderPath, "Temp_" + str(count) + ".pdf"))
    count = count + 1
    pageNum = pageNum + 1

# After the script is finished looping through each neighborhood, the final step is to save and close the PDF.
if count > 0:
    pdfDoc.saveAndClose()
os.startfile(os.path.join(outputFolderPath, pdfFileName))
arcpy.AddMessage("The script ran successfully!.")
