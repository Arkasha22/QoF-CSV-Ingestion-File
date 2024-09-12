# QoF-CSV-Ingestion-File

Python code designed to be run in ArcGIS OnLine Notebook

This allows users to import Quality and Outcomes Framework (QoF) data from PHE FingerTips (Open Source Data) and publish it as a Web Map Service.

It carries out the following actions in the following order

##QoF CSV Ingestion file created by Donald Maruta - 17 Apr 24  
 - Connect to AGOL  
 - Required Modules
 - This creates a unique date time code for trouble shooting
 - Sets up folder variables
 - Create File GDB
 - Get name of ZIP file - looks for a ZIP file in the arcgis/home/QoF folder which starts with QOF
 - Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with ACHIEVEMENT_LONDON
 - Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with MAPPING_INDICATORS
 - Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with MAPPING_NHS_GEOGRAPHIES
 - Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with PREVALENCE
 - Import nhsGeo Table into FGDB
 - Selection of GPs within NCL ICB
 - Define fields to keep
 - Get the data from the APIs and same them as CSV files
 - Convert GP CSV into FGDB
 - Create XY Feature Layer
 - Join Between nhsGeoFC and Prev
 - Join Between nhsGeoFCPrev and MapInd
 - Convert CSV into Pandas Dataframe
 - Pivot the DataFrame
 - Join Between nhsGeoFCPrevMapInd and AchLon
 - Get name of XLSX file - looks for a XLSX file in the arcgis/home/QoF folder which starts with qof
 - Add Join for Indicator Description
 - Convert FC to SHP for uploading to AGOL
 - Create Zip file
 - Initial Publish to AGOL
 - Code to delete unnecessary files
