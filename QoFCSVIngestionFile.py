##QoF CSV Ingestion file created by Donald Maruta - 17 Apr 24

#Note - it is necessary to download the latest Zipped QoF CSV File found here - https://digital.nhs.uk/data-and-information/publications/statistical/quality-and-outcomes-framework-achievement-prevalence-and-exceptions-data/2022-23 - QOF 2022-23: Raw Data .CSV files
#Note - change the year in the link above as required
#Note - it is necessary to upload the latest Zipped QoF CSV File to the /arcgis/home/QoF folder

#Connect to AGOL
from arcgis.gis import GIS
gis = GIS("home")

#Import Required Modules
import arcpy, os, glob, csv, requests, json, shutil, datetime, openpyxl, zipfile, io
from zipfile import ZipFile
import pandas as pd
arcpy.env.qualifiedFieldNames = False

#This creates a unique date time code for trouble shooting
todayDate = datetime.datetime.now().strftime("%y%m%d%y%H%M")
print(todayDate)

#Sets up folder variables
FGDBpath = '/arcgis/home/QoF/QoF' + todayDate + '.gdb'
fldrPath = '/arcgis/home/QoF/'

#Create File GDB
arcpy.CreateFileGDB_management(fldrPath, 'QoF' + todayDate + '.gdb')

#Get name of ZIP file - looks for a ZIP file in the arcgis/home/QoF folder which starts with QOF
zipFile = (glob.glob("/arcgis/home/QoF/QOF*.zip"))
strFile = str(zipFile) #Creates the file locations as a string
strFile = (strFile.strip("[']")) #Removes the ['] characters
print(strFile)

#Unzip the ZIP file
with zipfile.ZipFile(strFile, "r") as zip_ref:
    zip_ref.extractall(fldrPath)

#Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with ACHIEVEMENT_LONDON
csvFile = (glob.glob("/arcgis/home/QoF/ACHIEVEMENT_LONDON*.csv"))
achLon = str(csvFile) #Creates the file locations as a string
achLon = (achLon.strip("[']")) #Removes the ['] characters
print(achLon)

#Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with MAPPING_INDICATORS
csvFile = (glob.glob("/arcgis/home/QoF/MAPPING_INDICATORS*.csv"))
mapInd = str(csvFile) #Creates the file locations as a string
mapInd = (mapInd.strip("[']")) #Removes the ['] characters
print(mapInd)

#Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with MAPPING_NHS_GEOGRAPHIES
csvFile = (glob.glob("/arcgis/home/QoF/MAPPING_NHS_GEOGRAPHIES*.csv"))
nhsGeo = str(csvFile) #Creates the file locations as a string
nhsGeo = (nhsGeo.strip("[']")) #Removes the ['] characters
print(nhsGeo)

#Get name of CSV file - looks for a ZIP file in the arcgis/home/QoF folder which starts with PREVALENCE
csvFile = (glob.glob("/arcgis/home/QoF/PREVALENCE*.csv"))
prevTab = str(csvFile) #Creates the file locations as a string
prevTab = (prevTab.strip("[']")) #Removes the ['] characters
print(prevTab)

#Import nhsGeo Table into FGDB
tabNam = "nhsGeo"
outTab = os.path.join(FGDBpath, tabNam)

#Selection of GPs within NCL ICB
sqlExp = "ICB_NAME = 'NHS North Central London Integrated Care Board'"
tempTab = os.path.join(FGDBpath, "tempTab")
in_memory_table = arcpy.CopyRows_management(nhsGeo, out_table=r"in_memory\tbl")
arcpy.conversion.ExportTable(in_memory_table, tempTab, sqlExp)
arcpy.management.Delete(r"in_memory\tbl")

#Define fields to keep
fields_to_keep = ["PCN_ODS_CODE", "PCN_NAME", "PRACTICE_CODE", "PRACTICE_NAME"]

#Create a FieldMappings object
field_mappings = arcpy.FieldMappings()

#Add fields from CSV to the FieldMappings object
for field in arcpy.ListFields(tempTab):
    if field.name in fields_to_keep:
        #If the field is in the list of fields to keep, add it
        field_map = arcpy.FieldMap()
        field_map.addInputField(tempTab, field.name)
        field_mappings.addFieldMap(field_map)

#Convert CSV to geodatabase table using FieldMappings
arcpy.conversion.ExportTable(tempTab, outTab, "", "", field_mappings)

#List of datasets
datasets = [
    {
        'filter': "OrganisationTypeID eq 'GPB'", #GPs
        'orderby': "geo.distance(Geocode, geography'POINT(-0.15874 51.6116)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
#Add more datasets as needed
]

#Specify the file paths where you want to save the CSV files
csv_file_paths = [
    "/arcgis/home/QoF/GPB.csv",
    # Add more file paths as needed
]

#Get the data from the APIs and same them as CSV files
for dataset, csv_file_path in zip(datasets, csv_file_paths):
    response = requests.request(
        method='POST',
        url='https://api.nhs.uk/service-search/search?api-version=1',
        headers={
            'Content-Type': 'application/json',
            'subscription-key': '557d555fd712449f894e78e50a460000'
        },
        json=dataset
    )

    #Parse the response as JSON
    data = response.json()

    #Extract the required data from the JSON response
    output = []
    for item in data.get('value', []):
        output.append([
            item.get('NACSCode'),
            item.get('Postcode'),
            item.get('Latitude'),
            item.get('Longitude'),
        ])

    #Open the CSV file in write mode
    with open(csv_file_path, 'w', newline='') as csvfile:
        #Create a CSV writer object
        csv_writer = csv.writer(csvfile)

        #Write the header row
        csv_writer.writerow(['OCS_Code', 'Postcode', 'Latitude', 'Longitude'])

        #Write the output to the CSV file
        csv_writer.writerows(output)

    #Confirmation message
    print(f"Output saved as CSV: {csv_file_path}")

#Confirmation message
print("All datasets processed successfully.")

#Convert GP CSV into FGDB
input_table = "/arcgis/home/QoF/GPB.csv"
arcpy.conversion.TableToGeodatabase(input_table, FGDBpath)

#Field Join
arcpy.env.workspace = FGDBpath
tempdata = arcpy.management.AddJoin(outTab, "PRACTICE_CODE", "GPB", "OCS_Code")
arcpy.management.CopyRows(tempdata, "nhsGeo2")

#Delete Redundant Fields
arcpy.management.DeleteField("nhsGeo2", ["OBJECTID_1", "OCS_CODE"])

#Create XY Feature Layer
sr = arcpy.SpatialReference(4326)
arcpy.env.workspace = FGDBpath
arcpy.management.XYTableToPoint("nhsGeo2", "nhsGeoFC", "Longitude", "Latitude", "", sr)

#Convert GP CSV into FGDB & Get Name of Prev
arcpy.env.workspace = FGDBpath
arcpy.conversion.TableToGeodatabase(prevTab, FGDBpath)
tempFile = os.path.basename(prevTab)
tempFile = os.path.splitext(tempFile)
tempFile = tempFile[0]

#Join Between nhsGeoFC and Prev
tempdata = arcpy.management.AddJoin("nhsGeoFC", "PRACTICE_CODE", tempFile, "PRACTICE_CODE")
arcpy.management.CopyFeatures(tempdata, "nhsGeoFCPrev")
fc = arcpy.ListFeatureClasses()

#Delete Redundant Fields
arcpy.management.DeleteField("nhsGeoFCPrev", ["OBJECTID_1", "PRACTICE_CODE_1", "PRACTICE_CODE_X", "PRACTICE_CODE_Y"])

#Convert GP CSV into FGDB
arcpy.env.workspace = FGDBpath
arcpy.conversion.TableToGeodatabase(mapInd, FGDBpath)
tempFile = os.path.basename(mapInd)
tempFile = os.path.splitext(tempFile)
tempFile = tempFile[0]

#Join Between nhsGeoFCPrev and MapInd
tempdata = arcpy.management.AddJoin("nhsGeoFCPrev", "GROUP_CODE", tempFile, "GROUP_CODE")
arcpy.management.CopyFeatures(tempdata, "nhsGeoFCPrevMapInd")
fc = arcpy.ListFeatureClasses()

#Delete Redundant Fields
arcpy.management.DeleteField("nhsGeoFCPrevMapInd", ["OBJECTID_1", "GROUP_CODE_1"])

#Add PracInd Field
arcpy.management.CalculateField("nhsGeoFCPrevMapInd", "PRACIND", "!PRACTICE_CODE! + !INDICATOR_CODE!")

#Convert CSV into Pandas Dataframe
df = pd.read_csv(achLon)  

#Drop first three columns
df.drop(['REGION_ODS_CODE', 'REGION_ONS_CODE', 'REGION_NAME'], axis=1, inplace=True)

# Pivot the DataFrame
pivot_df = df.pivot(index=['PRACTICE_CODE', 'INDICATOR_CODE'], columns='MEASURE', values='VALUE').reset_index()

#Add a new column named PracInd
pivot_df['PracInd'] = pivot_df['PRACTICE_CODE'] + pivot_df['INDICATOR_CODE']

#Output the dataframe 
print(pivot_df)

#Save df as CSV
pivot_df.to_csv(achLon, index=False)

#Convert GP CSV into FGDB
arcpy.env.workspace = FGDBpath
arcpy.conversion.TableToGeodatabase(achLon, FGDBpath)
tempFile = os.path.basename(achLon)
tempFile = os.path.splitext(tempFile)
tempFile = tempFile[0]

#Join Between nhsGeoFCPrevMapInd and AchLon
tempdata = arcpy.management.AddJoin("nhsGeoFCPrevMapInd", "PRACIND", tempFile, "PracInd")
arcpy.management.CopyFeatures(tempdata, "nhsGeoFCPrevMapIndAch")
fc = arcpy.ListFeatureClasses()
print(fc)

#Delete Unnecessary Fields
arcpy.management.DeleteField("nhsGeoFCPrevMapIndAch", ["OBJECTID_1", "PRACTICE_CODE_1", "INDICATOR_CODE_1", "PracInd_1"])

#Get name of XLSX file - looks for a XLSX file in the arcgis/home/QoF folder which starts with qof
xlsxFile = (glob.glob("/arcgis/home/QoF/qof*.xlsx"))
strFile = str(xlsxFile) #Creates the file locations as a string
strFile = (strFile.strip("[']")) #Removes the ['] characters
print(strFile)

#Import XLSX worksheetfile into GDB
worksheet = "Table 1"
tempXLSX = os.path.join(FGDBpath, "tempXLSX")
arcpy.conversion.ExcelToTable(strFile, tempXLSX, worksheet, 10) # The last variable is the row from which the column names should be taken

#Drop unneeded fields
kpFields = ["Indicator", "Indicator_description"]
arcpy.management.DeleteField(tempXLSX, kpFields, "KEEP_FIELDS")

#Add Join for Indicator Description
tempdata = arcpy.management.AddJoin("nhsGeoFCPrevMapIndAch", "INDICATOR_CODE", tempXLSX, "Indicator")
arcpy.management.CopyFeatures(tempdata, "nhsGeoFCPrevMapIndAchDef")
fc = arcpy.ListFeatureClasses()

#Delete Unnecessary Fields
arcpy.management.DeleteField("nhsGeoFCPrevMapIndAchDef", ["REGISTER_1", "OBJECTID_1", "Indicator"])

#Convert FC to SHP for uploading to AGOL
finalName = "QoF_2223" #This will need to be changed for the current year
arcpy.management.Rename("nhsGeoFCPrevMapIndAchDef", finalName)
arcpy.conversion.FeatureClassToShapefile(finalName, fldrPath)

#List of files in complete directory
file_list = [finalName + ".shp", finalName + ".shx", finalName + ".dbf", finalName + ".prj"]
os.chdir(fldrPath)
                
#Create Zip file
shpzip = finalName + ".zip"
with zipfile.ZipFile(shpzip, 'w') as zipF:
    for file in file_list:
        zipF.write(file, compress_type=zipfile.ZIP_DEFLATED)

#Initial Publish to AGOL
item = gis.content.add({}, shpzip)
published_item = item.publish()
published_item.share(everyone=True)

#Code to delete unnecessary files
arcpy.env.workspace = '/arcgis/home/CancerDashboard'

# Get a list of all subdirectories (folders) in the specified folder
folders = [f for f in os.listdir(fldrPath) if os.path.isdir(os.path.join(fldrPath, f))]

for folder in folders:
    folder = os.path.join(fldrPath, folder)
    shutil.rmtree(folder)

#List of files to preserve
files_to_preserve = ['QoFMasterList.csv']

# Get a list of all files in the directory
all_files = glob.glob(os.path.join(fldrPath, "*"))

# Iterate over each file
for file_path in all_files:
    # Get the file name
    file_name = os.path.basename(file_path)
    
    # Check if the file name is not in the list of files to preserve
    if file_name not in files_to_preserve:
        # Delete the file
        os.remove(file_path)
        print(f"Deleted {file_name}")

print("All files except the specified ones have been deleted.")
