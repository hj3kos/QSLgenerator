import configparser
import tkinter as tk
import tksheet as tks
import os
import re
import requests
import smtplib

from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from io import BytesIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from PIL import ImageTk
from string import Template
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk 
import xmltodict

# Config file
config = configparser.ConfigParser()
config.read('config.ini')
# Invalid characters for filename
invalid = '<>:"/\|?* '
#Start form
root = tk.Tk()
root.iconbitmap("Icon.ico")
# QSL images start
qslimg=None
qslthumb=None
tkqslimg=None
# QRZ
qrz_host="https://xmldata.qrz.com/xml/1.36/"
qrz_token=""

# GENERAL FUNCTIONS

# QRZ Login Function
def qrz_login():
    global config
    global qrz_token
    r=requests.get(qrz_host+'?username='+config["qrz"]["username"]+';password='+config["qrz"]["password"]+
                   ';agent=QSLgenerator0.0.3')
    return xmltodict.parse(r.text)["QRZDatabase"]["Session"]["Key"]

# QRZ Callsign Lookup
def qrz_lookup_callsign(callsign):
    global qrz_token
    r=requests.get(qrz_host+'?s='+qrz_token+';callsign='+callsign)
    callsign_r = xmltodict.parse(r.text)
    return callsign_r

# Send email wgiven QSO info, QSL image using body field
# https://support.google.com/accounts/answer/185833
def send_email(imgtmp,qso,filename):
    global config
    buffer = BytesIO()
    imgtmp.save(buffer, format="PNG")
    buffer.seek(0)

    sender = config['email']['username']
    subject = "Test QSL email"
    body = Template(emailBody.get("1.0", tk.END)).safe_substitute(qso)
    try:
        # Configurar mensaje
        msg = MIMEMultipart()
        msg['From'] = config['email']['username']
        msg['To'] = qso["email"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))  # Cuerpo del mensaje en texto plano

        # Adjuntar la imagen
        adjunto = MIMEBase("application", "octet-stream")
        adjunto.set_payload(buffer.read())
        encoders.encode_base64(adjunto)
        adjunto.add_header(
            "Content-Disposition",
            f'attachment; filename="'+filename+'"'
        )
        msg.attach(adjunto)

        # Conexión al servidor SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Iniciar conexión segura
            server.login(config['email']['username'], config['email']['password'])  # Iniciar sesión
            server.send_message(msg)  # Enviar mensaje
    except Exception as e:
        pass
        tk.messagebox("Error al enviar correo a "+config['email'])

# Read the ADIF file and convert it to lists
def readADIF(importFile):
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

# Update QSL preview
def updateQslImage(discard):
    global qslimg

    qslimg2 = qslimg.convert("RGBA")
    qslimg2=drawTable(qslimg2,"HJ3KOS","01","01","2025","00:00","28.392000","59","59","SSB","Thanks for the contact. 73")
    qslthumb2 = qslimg2.resize((800,600))
    tkqslimg2 = ImageTk.PhotoImage(qslthumb2)
    labelQslImg.configure(image=tkqslimg2)
    labelQslImg.image=tkqslimg2

# Draw table over qsl image
def drawTable(newimg,call,day,month,year,utc,freq,rcp_recv,rcp_sent,mode,message):
    FONT_OPACITY = int(255 * scaleFontAlpha.get()/100)
    FONT_COLOR = _from_hex(btnFontColor.cget('bg'))
    TABLE_BGOPACITY = int(255 * scaleBgAlpha.get()/100)
    TABLE_BGCOLOR = _from_hex(btnBgColor.cget('bg'))
    TABLE_OUTOPACITY = int(255 * scaleBorderAlpha.get()/100)
    TABLE_OUTCOLOR = _from_hex(btnBorderColor.cget('bg'))
    font2 = ImageFont.truetype("Roboto-Regular.ttf", 28)

    overlay = Image.new('RGBA', newimg.size, FONT_COLOR+(0,))
    draw = ImageDraw.Draw(overlay) 
    font = ImageFont.truetype("Roboto-Regular.ttf", 40)

    # DRAW BOXES
    draw.rounded_rectangle(((100, 920), (1623, 1100)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3, radius=7)
    draw.rounded_rectangle(((100, 995), (360,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((360,995), (450,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((450,995), (530,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((530,995), (680,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((680,995), (880,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((880,995), (1140, 1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((1140,995), (1295,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((1295,995), (1450,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    draw.rounded_rectangle(((1450,995), (1623,1050)), fill=TABLE_BGCOLOR+(TABLE_BGOPACITY,),outline=TABLE_OUTCOLOR+(TABLE_OUTOPACITY,),width=3)
    # WRITE HEADERS
    draw.multiline_text((120,930),"CONFIRMING QSO\n WITH",fill=FONT_COLOR+(FONT_OPACITY,),font=font2,align='center')
    draw.multiline_text((370,930),"DATE\nDD       MM     YYYY",fill=FONT_COLOR+(FONT_OPACITY,),font=font2,align='center')
    draw.multiline_text((690,940),"UTC",fill=FONT_COLOR+(FONT_OPACITY,),font=font,align='center')
    draw.multiline_text((890,940),"MHz",fill=FONT_COLOR+(FONT_OPACITY,),font=font,align='center')
    draw.multiline_text((1190,930),"RCP\nSENT          RCVD",fill=FONT_COLOR+(FONT_OPACITY,),font=font2,align='center')
    draw.multiline_text((1480,940),"MODE",fill=FONT_COLOR+(FONT_OPACITY,),font=font,align='center')
    # WRITE QSO INFO
    draw.text((120,1000),call,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((380,1000),day,fill=FONT_COLOR+(FONT_OPACITY,),font=font)  
    draw.text((470,1000),month,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((550,1000),year,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((700,1000),utc,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((900,1000),freq,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((1185,1000),rcp_sent,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((1340,1000),rcp_recv,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((1495,1000),mode,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    draw.text((120,1050),message,fill=FONT_COLOR+(FONT_OPACITY,),font=font)
    newimg = Image.alpha_composite(newimg, overlay)
    return newimg

# Generate image files or send emails
def generateQsl(email):
    global qslimg

    headers=[x.lower() for x in sheet.headers()]
    for qso in sheet.data:
        qso = dict(zip(headers, qso))
        day = str(qso["qso_date"][6:])
        month =  str(qso["qso_date"][4:6])
        year =  str(qso["qso_date"][:4])
        call = str(qso["call"])
        utc =  str(qso["time_on"][:2]+':'+qso["time_on"][2:4])
        freq =  str(qso["freq"])
        if qso["qsl_message"]!="":
            message=qso["qsl_message"]
        else:
            message="Thanks for the contact. 73"
        try:
            rcp_recv =  str(qso["rst_rcvd"])
            int(rcp_recv)
        except:
            rcp_recv = "59"
        try:
            rcp_sent =  str(qso["rst_sent"])
            int(rcp_sent)
        except:
            rcp_sent = "59"
        mode =  str(qso["mode"])
        if mode.lower() == "digitalvoice":
            mode = "D.VOICE"

        imgtmp=drawTable(qslimg,call,day,month,year,utc,freq,rcp_recv,rcp_sent,mode,message)
        #SAVE
        filename=call+'_'+day+'_'+month+'_'+year+'_'+utc+'.png'
        for char in invalid:
            filename = filename.replace(char, '-')
        if not email:
            imgtmp.save(config["images"]["output_folder"]+'/'+filename)
        #SEND BY EMAIL
        else:
            if config["email"]["username"] == "" or config["email"]["password"]=="":
                tk.messagebox.showerror(title="Email Error",message="No email account configured")
                return
            if qso["email"] == "email" or qso["email"]==None:
                continue
            else:
                send_email(imgtmp,qso,filename)

# Converts colors from hech to int
def _from_rgb(rgb):
    return "#%02x%02x%02x" % rgb  

# Converts colors from int to hex
def _from_hex(hex):
    hex = hex.lstrip('#')
    r = int(hex[0:2], 16)  # Rojo
    g = int(hex[2:4], 16)  # Verde
    b = int(hex[4:6], 16)  # Azul
    return (r, g, b)

# Form to choose color for QSL
def choose_color(button):
    color_code = colorchooser.askcolor(title ="Choose color") 
    button.configure(bg=_from_rgb(color_code[0]))
    updateQslImage(None)

# Get emails from web service
def fill_emails():
    global config
    global qrz_token
    if config["qrz"]["username"] == "" or config["qrz"]["password"]=="":
        tk.messagebox.showerror(title="QRZ Error",message="No QRZ account account configured")
        return
    qrz_token = qrz_login()
    row=0
    headers=[x.lower() for x in sheet.headers()]
    for qso in sheet.data:
        qso = dict(zip(headers, qso))
        if qso["email"]=="" or qso["email"]=="email":
            callsign_r = qrz_lookup_callsign(qso["call"])["QRZDatabase"]
            if "Callsign" not in callsign_r:
                tk.messagebox.showerror(title="QRZ Error",message="Not found "+qso["call"])
            elif "email" not in callsign_r["Callsign"]:
                ttk.messagebox.showerror(title="QRZ Error",message="No email registered for "+qso["call"])
            else:
                column=sheet.headers().index("email")
                sheet.set_cell_data(row,column,callsign_r["Callsign"]["email"])
        else:
            pass
        row+=1

# Function Called When Load ADIF in menu is pressed
def file_loadadif_press():
    adif_file_path = filedialog.askopenfilename(filetypes=[("ADIF Logbook File", ".adi .adif")])
    data,header=readADIF(adif_file_path)
    sheet.headers(header[0])
    sheet.data=data
    if "email" not in [x.lower() for x in header[0]]:
        sheet.insert_column()
        sheet.headers(header[0]+["email"])
        header[0]=header[0]+["email"]
    if "qsl_message" not in [x.lower() for x in header[0]]:
        sheet.insert_column()
        sheet.headers(header[0]+["qsl_message"])
    tabControl.tab(1, state="normal")
    # TO-DO Checkboxes

# Function Called When Load Image in menu is pressed
def file_loadimage_press():
    global qslimg

    image_file_path = filedialog.askopenfilename(filetypes=[("Image File", ".jpeg .jpg .png")])
    qslimg = Image.open(image_file_path).convert("RGBA")
    qslimg = qslimg.convert("RGBA").resize((1800, 1200))
    updateQslImage(None)
    tabControl.tab(2, state="normal")
    btnGenerateImages.config(state="normal")

# Function Called When exit in menu is pressed
def file_exit_press():
    root.destroy() 
    
# Function Called When About in menu is pressed
def help_about_press():
    modal = tk.Toplevel()
    modal.iconbitmap("Icon.ico")
    modal.title("About")
    modal.geometry("600x400")
    modal.resizable(False, False)
    modal.transient()
    modal.grab_set()
    frame = ttk.Frame(modal, padding="10")
    frame.grid(sticky=(tk.W, tk.E, tk.N, tk.S))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    try:
        img1 = Image.open("HJ3KOS.png").resize((200, 200))
        img2 = Image.open("RAU.jpg").resize((200, 200))
        photo1 = ImageTk.PhotoImage(img1)
        photo2 = ImageTk.PhotoImage(img2)
    except FileNotFoundError:
        tk.messagebox.showerror(title="Error",message="Make sure the files exist")
        return
    img_frame = ttk.Frame(frame)
    img_frame.grid(row=0, column=0, pady=10)
    img_label1 = ttk.Label(img_frame, image=photo1)
    img_label1.image = photo1  
    img_label1.grid(row=0, column=0, padx=10)
    img_label2 = ttk.Label(img_frame, image=photo2)
    img_label2.image = photo2
    img_label2.grid(row=0, column=1, padx=10)
    text_label = ttk.Label(frame, text="Developed by: HJ3KOS", 
                           font=("Arial", 12), anchor="center", justify="center")
    text_label.grid(row=1, column=0, pady=10)
    close_button = ttk.Button(frame, text="Cerrar", command=modal.destroy)
    close_button.grid(row=2, column=0, pady=20)
    frame.pack(expand=True, fill="both")
    modal.protocol("WM_DELETE_WINDOW", modal.destroy)
    modal.mainloop()

# Save configuration changes
def save_configuration(username,password,qrz_username,qrz_password,path):
    global config
    # set new value
    config.set('email', 'username',username )
    config.set('email', 'password',password )
    config.set('qrz', 'username',qrz_username )
    config.set('qrz', 'password',qrz_password )
    config.set('images', 'output_folder',path )

    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    messagebox.showinfo("successfully Saved", f"Configuration successfully saved.")

# Set Images Output folder from config dialog
def seleccionar_ruta(entry_ruta):   
    # Abrir un cuadro de diálogo para seleccionar la carpeta
    ruta = filedialog.askdirectory()
    if ruta:
        entry_ruta.delete(0, tk.END)  # Limpiar campo actual
        entry_ruta.insert(0, ruta)  # Insertar la nueva ruta seleccionada

# Configuration form
def file_config_press():
    global config

    modal = tk.Toplevel()
    modal.iconbitmap("Icon.ico")
    modal.title("About")
    modal.resizable(False, False)
    modal.transient()
    modal.grab_set()
    frame = ttk.Frame(modal, padding=10)
    frame.pack(fill="both", expand=True)

    # Email user
    ttk.Label(frame, text="Gmail email:").grid(row=0, column=0, sticky="w", pady=5)
    entry_user_email = ttk.Entry(frame, width=30)
    entry_user_email.grid(row=0, column=1, pady=5)
    entry_user_email.insert(0, config["email"]["username"])
    # Email app password
    ttk.Label(frame, text="Gmail app password:").grid(row=1, column=0, sticky="w", pady=5)
    entry_password_email = ttk.Entry(frame, show="*", width=30)
    entry_password_email.grid(row=1, column=1, pady=5)
    entry_password_email.insert(0, config["email"]["password"])
    # Spacer
    ttk.Label(frame, text="").grid(row=3, column=0, sticky="w", pady=10)
    # QRZ User
    ttk.Label(frame, text="QRZ user:").grid(row=4, column=0, sticky="w", pady=5)
    entry_user_qrz = ttk.Entry(frame, width=30)
    entry_user_qrz.grid(row=4, column=1, pady=5)
    entry_user_qrz.insert(0, config["qrz"]["username"])
    # QRZ Password
    ttk.Label(frame, text="QRZ password:").grid(row=5, column=0, sticky="w", pady=5)
    entry_password_qrz = ttk.Entry(frame, show="*", width=30)
    entry_password_qrz.grid(row=5, column=1, pady=5)
    entry_password_qrz.insert(0, config["qrz"]["password"])
    # Images output folder
    ttk.Label(frame, text="Images Output Folder:").grid(row=6, column=0, sticky="w", pady=5)
    entry_path = ttk.Entry(frame, width=30)
    entry_path.grid(row=6, column=1, pady=20)
    entry_path.insert(0, config["images"]["output_folder"])
    # Botón para seleccionar ruta
    button_ruta = ttk.Button(frame, text="Select", command=lambda: seleccionar_ruta(entry_path))
    button_ruta.grid(row=6, column=2, padx=20)

    # Save configuration
    button_save = ttk.Button(frame, text="Save Configuration",
                             command=lambda: save_configuration(entry_user_email.get(),
                                                                entry_password_email.get(),
                                                                entry_user_qrz.get(),
                                                                entry_password_qrz.get(),
                                                                entry_path.get()))
    button_save.grid(row=7, column=0, pady=20)
    frame.pack(expand=True, fill="both")
    modal.protocol("WM_DELETE_WINDOW", modal.destroy)
    modal.mainloop()

# Clear the application
def file_newwork_press():
    answer=tk.messagebox.askyesno(
        message="This would clear all the information.\nDo you want to continue?",
        title="New Work"
    )
    if answer:
        img=None
        qslthumb=None
        tkqslimg=None
        sheet.headers([])
        sheet.data=[]
        labelQslImg.image=None
        tabControl.tab(1, state="disabled")
        tabControl.tab(2, state="disabled")
    else:
        pass

#############
# INTERFACE #
#############
root.title("QSLgenerator")
root.config(width=400, height=300)
root.state('zoomed')
menu_bar = tk.Menu()
# File Menu
menu_file = tk.Menu(menu_bar, tearoff=False)
menu_file.add_command(
    label="New Work",
    accelerator="Ctrl+A",
    command=file_newwork_press
)
menu_file.add_command(
    label="Configuration",
    accelerator="Ctrl+Alt+C",
    command=file_config_press
)
menu_file.add_command(
    label="Exit",
    accelerator="Ctrl+X",
    command=file_exit_press
)
menu_bar.add_cascade(menu=menu_file, label="File")

# Help Menu
menu_help = tk.Menu(menu_bar, tearoff=False)
#menu_help.add_command(
#    label="How-To",
#    command=help_about_press
#)
menu_help.add_command(
    label="About",
    command=help_about_press
)
menu_bar.add_cascade(menu=menu_help, label="Help")

# TABS
tabControl = ttk.Notebook(root) 
  
tab1 = ttk.Frame(tabControl) #ADIF TAB
tab2 = ttk.Frame(tabControl) #QSL TAB
tab3 = ttk.Frame(tabControl) #EMAIL TAB

tabControl.add(tab1, text ='ADIF') 
tabControl.add(tab2, text ='QSL Preview') 
tabControl.add(tab3, text ='EMAIL') 
tabControl.tab(1, state="disabled")
tabControl.tab(2, state="disabled")
tabControl.pack(expand=True, fill=tk.BOTH)

# TAB 1 ADIF
tab1.columnconfigure(0, weight=1)
tab1.rowconfigure(0, weight=1)

sheet = tks.Sheet(tab1)
sheet.enable_bindings()
sheet.grid(row=0,column=0,sticky="nsew")


tab1_button_frame = ttk.Frame(tab1)
tab1_button_frame.grid(row=0, column=1, padx=10, pady=10)
                  
btnLoadAdif=tk.Button(tab1_button_frame,text='Load ADIF', command=file_loadadif_press)
btnLoadAdif.grid(row=0,column=0, pady=5)
btnFillEmails=tk.Button(tab1_button_frame,text='Fill Emails', command=fill_emails)
btnFillEmails.grid(row=1,column=0, pady=5)

# TAB 2 IMAGE
tab2.columnconfigure(0, weight=1)
tab2.rowconfigure(0, weight=1)

labelQslImg = tk.Label(tab2,image=None)
labelQslImg.grid(row=0,column=0,sticky="nsew")

tab2_button_frame = ttk.Frame(tab2)
tab2_button_frame.grid(row=0, column=1, padx=10, pady=10)

btnLoadImg=tk.Button(tab2_button_frame,text='Load Image', command=file_loadimage_press)
btnLoadImg.grid(row=0,column=1, pady=5,columnspan=2)

ttk.Label(tab2_button_frame, text="Font Color:").grid(row=1, column=1, sticky="w", pady=5)
btnFontColor=tk.Button(tab2_button_frame,text='   ',bg="#000000", command=lambda: choose_color(btnFontColor))
btnFontColor.grid(row=1,column=2, pady=5)
scaleFontAlpha = tk.Scale(tab2_button_frame, from_=0, to=100, orient="horizontal", command=updateQslImage)
scaleFontAlpha.grid(row=2,column=1, pady=5,columnspan=2)
scaleFontAlpha.set(75)
ttk.Label(tab2_button_frame, text="Border Color:").grid(row=3, column=1, sticky="w", pady=5)
btnBorderColor=tk.Button(tab2_button_frame,text='   ',bg="#000000", command=lambda: choose_color(btnBorderColor))
btnBorderColor.grid(row=3,column=2, pady=5)
scaleBorderAlpha = tk.Scale(tab2_button_frame, from_=0, to=100, orient="horizontal", command=updateQslImage)
scaleBorderAlpha.grid(row=4,column=1, pady=5,columnspan=2)
scaleBorderAlpha.set(75)
ttk.Label(tab2_button_frame, text="Background Color:").grid(row=5, column=1, sticky="w", pady=5)
btnBgColor=tk.Button(tab2_button_frame,text='   ',bg="#ffffff", command=lambda: choose_color(btnBgColor))
btnBgColor.grid(row=5,column=2, pady=5)
scaleBgAlpha = tk.Scale(tab2_button_frame, from_=0, to=100, orient="horizontal", command=updateQslImage)
scaleBgAlpha.grid(row=6,column=1, pady=5,columnspan=2)
scaleBgAlpha.set(50)

btnGenerateImages=tk.Button(tab2_button_frame,text='Generate Images', command=lambda: generateQsl(False))
btnGenerateImages.config(state="disabled")
btnGenerateImages.grid(row=7,column=1, pady=5,columnspan=2)

# TAB 3 EMAIL
tab3.columnconfigure(0, weight=1)
tab3.rowconfigure(0, weight=1)

emailBody = tk.Text(tab3, width=20, height=3) 
emailBody.grid(column=0, row=0,sticky="nsew") 

tab3_button_frame = ttk.Frame(tab3)
tab3_button_frame.grid(row=0, column=1, padx=10, pady=10)

insert_text = """$call

Thank you for the QSO. Please find my QSL card attached. 

$operator

Contact Data
Call: $call from $operator
Date: $qso_date $time_on UTC
Freq: $freq
Band: $band
Mode: $mode
RSTS: $rst_sent
RSTR: $rst_rcvd
"""
  
emailBody.insert(tk.END, insert_text) 

btnSendEmails=tk.Button(tab3_button_frame,text='Send emails', command=lambda: generateQsl(True))
btnSendEmails.grid(row=0,column=0, pady=5)

root.config(menu=menu_bar)
root.mainloop()
