import csv
import os
import re
import sys
import time
import tkinter as tk
from datetime import date
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from PIL import ImageTk
from tkinter import filedialog

path_foto = ''
headers=[]
TINT_COLOR = (0, 0, 0)  # Black
TRANSPARENCY = .65  # Degree of solidity, 0-100%
OPACITY = int(255 * TRANSPARENCY)
invalid = '<>:"/\|?* '

def ReadADIF (importFile):
    adif = open(importFile, 'r')
    logLines = adif.readlines()

    ##########SETUP LISTS AND NAME OF FILE TO SAVE##########
    ##########SAVES IN SAME FOLDER AS THIS CODE##########
    header = []
    data = []
    headerRow = []
    dataRow = []
    tempLines = []
    tempQso = []

    ##########START THE BUILD##########
    #do a quick cleanup of the log and figure out which line to start after header info,
    for x in range(len(logLines)):
        logLines[x] = logLines[x].strip()
        logLines[x] = logLines[x].replace("\t", "")
        logLines[x] = logLines[x].replace("\n", "")
     
    #Go through all lines, and slit/append new ones where multiple tags found on one line.
    #show progress


    for x in range(len(logLines)):
        #add your own fields in comments or notes by using (()) to create the field
        logLines[x] = logLines[x].replace("((", "Xtra Field <")    
        logLines[x] = logLines[x].replace("))", ":>")
        #find the tags
        findTags = re.findall('<[^<]*?>', logLines[x])
        for y in range(len(findTags)):
            logLines[x] = logLines[x].replace(findTags[y], "<<" + findTags[y])
        newLines = logLines[x].split("<<")
        if len(newLines) > 0:
            for z in range(len(newLines)):
                tempLines.append(newLines[z])


    logLines = tempLines
    while("" in logLines):
        logLines.remove("")    

    #find end of header
    fstart = 0
    for x in range(len(logLines)):
        test = (str(logLines[x])).lower().find("<eoh>")
        if test != -1:
            fstart = x + 1
            x = len(logLines) + 1

    #build header (aka first row) and cycle through all the lines to make sure all fields are picked up
    for x in range(fstart, len(logLines)):
        if (str(logLines[x])).lower() != "<eor>":
            logLines[x] = logLines[x].split(":")
            logLines[x][0] = logLines[x][0].replace("<", "")
            if logLines[x][0] not in headerRow:
                headerRow.append(logLines[x][0])
    headerRow.sort()
    header.append(headerRow)
    #build rows, and add to data to matching column
    #row needs to be sorted to match header
    tempQso = headerRow.copy()
    for x in range(fstart, len(logLines)):
        
        if (str(logLines[x])).lower() != "<eor>":
            tester = 0
            #get rows in qso, sort in a tempQso
            for z in range(len(tempQso)):
                test = str(logLines[x]).find(str(tempQso[z]))
                if test == 2:
                    tempQso[z] = str(logLines[x])
                        
        if (str(logLines[x])).lower() == "<eor>":
            #append to dataRow
            for y in range(len(tempQso)):
                qsoData = ""
                qsoData = qsoData + str(tempQso[y]).split(">")[-1]
                qsoData = qsoData.replace("']", "")
                dataRow.append(str(qsoData))
            data.append(dataRow)
            dataRow = []
            tempQso = headerRow.copy()
    return data,header

def Generador_Imagenes( dia,
                        mes,
                        anio,
                        licencia,
                        hora,
                        mhz,
                        sent,
                        rcvd,
                        mode
                        ):
    global path_foto
     
    img = Image.open(path_foto.name)
    img = img.convert("RGBA").resize((1800, 1200))
    overlay = Image.new('RGBA', img.size, TINT_COLOR+(0,))
    draw = ImageDraw.Draw(overlay) 
    font = ImageFont.truetype("Roboto-Regular.ttf", 40)
    font2 = ImageFont.truetype("Roboto-Regular.ttf", 28)

    draw.rounded_rectangle(((100, 820), (1623, 1000)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3, radius=7)
    draw.rounded_rectangle(((100, 895), (360,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((360,895), (450,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((450,895), (530,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((530,895), (680,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((680,895), (880,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((880,895), (1140, 950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((1140,895), (1280,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((1280,895), (1450,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    draw.rounded_rectangle(((1450,895), (1623,950)), fill=(255,255,255)+(OPACITY,),outline=(0, 0, 0)+(OPACITY,),width=3)
    
    draw.multiline_text((120,830),"CONFIRMING QSO\n WITH",fill=(0,0,0)+(OPACITY,),font=font2,align='center')
    draw.multiline_text((370,830),"DATE\nDD       MM     YYYY",fill=(0,0,0)+(OPACITY,),font=font2,align='center')
    draw.multiline_text((690,840),"UTC",fill=(0,0,0)+(OPACITY,),font=font,align='center')
    draw.multiline_text((890,840),"MHz",fill=(0,0,0)+(OPACITY,),font=font,align='center')
    draw.multiline_text((1150,830),"RCP\nSENT          RCVD",fill=(0,0,0)+(OPACITY,),font=font2,align='center')
    draw.multiline_text((1460,840),"MODE",fill=(0,0,0)+(OPACITY,),font=font,align='center')
    
    draw.text((120,900),licencia,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((370,900),dia,fill=(63,81,181)+(OPACITY,),font=font)  
    draw.text((460,900),mes,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((540,900),anio,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((690,900),hora,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((890,900),mhz,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((1150,900),sent,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((1290,900),rcvd,fill=(63,81,181)+(OPACITY,),font=font)
    draw.text((1460,900),mode,fill=(63,81,181)+(OPACITY,),font=font)
    
    draw.multiline_text((120,960),msgTextBox.get("1.0","end-1c"),fill=(0,0,0)+(OPACITY,),font=font2,align='center')
    
    img = Image.alpha_composite(img, overlay)
    isExist = os.path.exists("qsl")
    if not isExist:
       os.makedirs("qsl")

    filename=licencia+'_'+anio+'_'+mes+'_'+dia+'.png'
    for char in invalid:
        filename = filename.replace(char, '-')
    img.save("qsl/"+filename)


def getAdif ():
    import_file_path = filedialog.askopenfilename()
    shape,headers = ReadADIF (import_file_path)
    headers=[x.lower() for x in headers[0]]
    cantidad = len(shape)
    print(cantidad)
    for i in range(0,cantidad):
        print(shape[i])
        dia = str(shape[i][headers.index("qso_date")][6:])
        mes =  str(shape[i][headers.index("qso_date")][4:6])
        anio =  str(shape[i][headers.index("qso_date")][:4])
        licencia = str(shape[i][headers.index("call")])
        hora =  str(shape[i][headers.index("time_on")][:2]+':'+shape[i][headers.index("time_on")][2:4])
        mhz =  str(shape[i][headers.index("freq")])
        rcvd =  str(shape[i][headers.index("rst_rcvd")])
        sent =  str(shape[i][headers.index("rst_sent")])
        mode =  str(shape[i][headers.index("mode")])
        print(dia+''+mes+''+anio+''+licencia+''+hora+''+mhz+''+sent+''+rcvd+''+mode)
        Generador_Imagenes(dia,mes,anio,licencia,hora,mhz,sent,rcvd,mode)

def getImage ():
        global path_foto
        path_foto = filedialog.askopenfile()
        print(path_foto.name)

root= tk.Tk()
root.resizable(0, 0)
root.title("QSL Card Generator")

canvas1 = tk.Canvas(root, width = 800, height = 600)
canvas1.pack()

loadImageButton = tk.Button(text='Load Image', command=getImage, font=('helvetica', 12, 'bold'))
loadImageButton.pack()
loadAdifButton = tk.Button(text='Load ADIF', command=getAdif, font=('helvetica', 12, 'bold'))
loadAdifButton.pack()
msgTextBox = tk.Text(root, height = 1, width = 20)
msgTextBox.pack()
imgLabel = tk.Label(text = "Recomended resolution for images is 1800x1200 pixels and PNG format.")
msgLabel = tk.Label(text = "Bottom Message.")

canvas1.create_window(400, 50, window=imgLabel)
canvas1.create_window(400, 75, window=msgLabel)
canvas1.create_window(400, 100, window=msgTextBox)
canvas1.create_window(400, 150, window=loadImageButton)
canvas1.create_window(400, 200, window=loadAdifButton)

root.mainloop()
