import tkinter as TK
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import sys
import threading
from PIL import Image
import os
import subprocess
from pdf2image import convert_from_path
from fpdf import FPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import datetime

class image_converer:
    def __init__(self):
        self.reset()
        self.settings = {}
        self.load_settings()
        self.conversion_happened = False
        self.setup_gui()
    
    def setup_gui(self):
        # main window
        root = TK.Tk()
        W = 320*4
        H = 240*3
        root.geometry(str(W)+"x"+str(H))
        root.minsize(320,240)
        self.title = "Image Converer v2.0"
        root.title(self.title)
        root.iconbitmap("favicon.ico")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # main frame
        frame = Frame(root)
        frame.grid(row=0, column=0, sticky="NEWS", padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)

        # destination location settings
        destination_location_label = Label(frame, text="Destination location:")
        destination_location_label.grid(row=0, column=0, sticky="W")
        sv = StringVar()
        sv.trace("w", self.change_dst_loc)
        self.destination_location = Entry(frame, textvariable=sv)
        self.destination_location.grid(row=0, column=1, sticky="EW", padx=5)
        self.destination_location_edit = Button(frame, text="Browse...", command=self.select_folder)
        self.destination_location_edit.grid(row=0, column=2, sticky="EW")
        self.destination_location.insert(END, self.settings["Destination"])

        # help button
        help_button = Button(frame, text="Help", command=self.help)
        help_button.grid(row=0, column=3, sticky="W", padx=(10,0))

        # convert to type
        convert_to_label = Label(frame, text="Convert to:")
        convert_to_label.grid(row=1, column=0, sticky="W")
        options_list = ["jpeg", "png", "bmp", "tiff", "Single pdf", "Combined pdf"]
        self.filetype_selected_value = StringVar(root)
        if not self.settings["Conver to"] in options_list:
            setto = options_list[0]
            self.edit_settings("Conver to", setto)
        else:
            setto = self.settings["Conver to"]
        self.filetype_selected_value.set(setto)
        self.convert_to_button = OptionMenu(frame, self.filetype_selected_value, *options_list)
        self.filetype_selected_value.trace("w", self.change_format)
        self.convert_to_button.grid(row=1, column=1, sticky="W")

        # files list
        self.selected_files_button = Button(frame, text="Select files...", command=self.choose_files)
        self.selected_files_button.grid(row=2, column=0, sticky="W", pady=(0,10))
        selected_files_frame = Frame(frame)
        selected_files_frame.grid(row=3, column=0, sticky="NEWS", columnspan=4)
        selected_files_frame.columnconfigure(0, weight=1)
        selected_files_frame.rowconfigure(0, weight=1)
        self.selected_files_list = Listbox(selected_files_frame, selectmode=MULTIPLE)
        self.selected_files_list.bind("<Delete>", self.delete_item)
        self.selected_files_list.grid(row=0, column=0, sticky="NEWS")
        selected_files_list_scrollbar = Scrollbar(selected_files_frame)
        selected_files_list_scrollbar.grid(row=0, column=1, sticky="NEWS")
        self.selected_files_list.config(yscrollcommand = selected_files_list_scrollbar.set)
        selected_files_list_scrollbar.config(command = self.selected_files_list.yview)
        
        # convert button
        self.convert_button = Button(selected_files_frame, text="CONVERT", command=self.convert)
        self.convert_button.grid(row=1, column=0, columnspan=4, sticky="NEWS", pady=(10, 0))

        # run
        root.mainloop()

    def choose_files(self):
        if self.conversion_happened:
            self.selected_files_list.configure()
            self.selected_files_list.delete(0, END)
            self.conversion_happened = False
            self.convert_button.configure(state=NORMAL)
            self.selected_files_list.configure(selectmode=MULTIPLE)

        files = filedialog.askopenfilenames(title="Select files")
        for file in files:
            self.selected_files_list.insert(END, file)
            self.selected_files_list.see(END)
    
    def convert(self):
        # start thread
        self.thread = threading.Thread(target=self.start_converting)
        self.thread.daemon = True
        self.thread.start()
    
    def start_converting(self):
        # disable buttons
        self.selected_files_list.selection_clear(0, END)
        self.selected_files_list.configure(state=DISABLED)
        self.destination_location_edit.configure(state=DISABLED)
        self.convert_to_button.configure(state=DISABLED)
        self.selected_files_button.configure(state=DISABLED)
        self.convert_button.configure(state=DISABLED)
        self.destination_location.configure(state=DISABLED)
        self.conversion_happened = True

        # go over each item in list
        for i, listbox_entry in enumerate(self.selected_files_list.get(0, END)):
            input_path = self.selected_files_list.get(i)
            filename = input_path.replace("\\", "/")
            filename = filename.split("/")
            filename = filename[-1]
            filename = filename.split(".")
            filename = filename[:-1]
            filename = ".".join(filename)
            formatt = self.settings["Conver to"]
            if formatt != "Single pdf" and formatt != "Combined pdf":
                output_path = self.settings["Destination"]+"/"+filename+"."+formatt
                data = self.save_img(input_path, output_path, formatt)
            else:
                if formatt == "Single pdf":
                    output_path = self.settings["Destination"]+"/"+filename+".pdf"
                    data = self.save_pdf(input_path, output_path)
                elif formatt == "Combined pdf":
                    data = self.add_to_combined_pdf(input_path)
            text = data[0]
            color = data[1]
            self.selected_files_list.configure(state=NORMAL)
            self.selected_files_list.delete(i)
            self.selected_files_list.insert(i, text)
            if color == "GOOD":
                self.selected_files_list.itemconfig(i, {'bg':'green', 'fg':'white'})
            elif color == "BAD":
                self.selected_files_list.itemconfig(i, {'bg':'red'})
            self.selected_files_list.configure(state=DISABLED)
        
        # convert to pdf
        if formatt == "Combined pdf":
            output_path = self.settings["Destination"]+"/"+self.today()+"_combined.pdf"
            data = self.save_combined_pdf(output_path)
            text = data[0]
            color = data[1]
            if color == "GOOD":
                messagebox.showinfo("Info","Done!")
            elif color == "BAD":
                self.error(text)
        else:
            # conversion over
            messagebox.showinfo("Info","Done!")
        self.selected_files_list.configure(state=NORMAL)
        self.selected_files_list.configure(selectmode=SINGLE)
        self.selected_files_list.configure(state=NORMAL)
        self.destination_location_edit.configure(state=NORMAL)
        self.convert_to_button.configure(state=NORMAL)
        self.selected_files_button.configure(state=NORMAL)
        self.destination_location.configure(state=NORMAL)
        self.open_folder(self.settings["Destination"])
        self.reset()

    def save_img(self, input_path, output_path, dst_format):
        return_text = ""

        # image to image
        if not ".PDF" in input_path.upper():
            try:
                # Open the image
                with Image.open(input_path) as img:
                    # Save the image
                    output_path = self.get_unique_name(output_path)
                    img.save(output_path, dst_format)
                    return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")
        
        # pdf to image
        else:
            try:
                poppler_path = "poppler-24.08.0/Library/bin"
                images = convert_from_path(input_path,poppler_path = poppler_path)

                for i, image in enumerate(images):
                    output_path = self.get_unique_name(output_path)
                    image.save(output_path, dst_format)
                    return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")

        # result
        return return_text
    
    def save_pdf(self, input_path, output_path):
        return_text = ""

        if not ".PDF" in input_path.upper():
            try:
                self.create_pdf_page(input_path)
                self.add_an_image_to_pdf_file(input_path)
                #self.pdf.image(input_path,0,0,320,240)
                output_path = self.get_unique_name(output_path)
                self.pdf.output(output_path, "F")
                return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
                self.pdf = FPDF()
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")
        else:
            try:
                os.makedirs(output_path, exist_ok=True)

                # Read the PDF
                reader = PdfReader(input_path)
                for page_num, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)

                    # Create an output file name for each page
                    output_file = os.path.join(output_path, f"page_{page_num}.pdf")

                    # Write the page to a file
                    with open(output_file, "wb") as output_pdf:
                        writer.write(output_pdf)
                    
                    return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")
        # result
        return return_text
    
    def add_to_combined_pdf(self, input_path):
        return_text = ""
        
        # for images
        if not ".PDF" in input_path.upper():
            try:
                self.create_pdf_page(input_path)
                self.add_an_image_to_pdf_file(input_path)
                #self.pdf.image(input_path,0,0,320,240)
                return_text = (input_path+" added to combined pdf file","GOOD")
                self.combine_img_to_pdf = True
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")
        
        # for pdf files
        else:
            try:
                self.merger.append(open(input_path, 'rb'))
                return_text = (input_path+" added to combined pdf file","GOOD")
                self.combine_pdf_to_pdf = True
            except Exception as e:
                return_text = (input_path+" Error: "+str(e), "BAD")
        # result
        return return_text

    def save_combined_pdf(self, output_path):
        return_text = ""
        
        # for images
        if self.combine_img_to_pdf:
            try:
                output_path = self.get_unique_name(output_path)
                self.pdf.output(output_path, "F")
                #return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
                self.pdf = FPDF()
                return_text = ("Saved as: "+output_path,"GOOD")
            except Exception as e:
                return_text = ("Error: "+str(e), "BAD")
        
        # for pdf files
        if self.combine_pdf_to_pdf:
            try:
                output_path = self.get_unique_name(output_path)
                with open(output_path, "wb") as fout:
                    self.merger.write(fout)
                return_text = ("Saved as: "+output_path,"GOOD")
            except Exception as e:
                return_text = ("Error: "+str(e), "BAD")

        # result
        return return_text

    def create_pdf_page(self, input_path):
        cover = Image.open(input_path)
        width, height = cover.size
        orientation = 'P' if width < height else 'L'
        self.pdf.add_page(orientation = orientation)

    def add_an_image_to_pdf_file(self, input_path):
        im = Image.open(input_path)
        width, height = im.size
        self.pdf.author = self.title
        self.pdf.b_margin = 10
        orientation = 'P' if width < height else 'L'
        width, height = float(width * 0.264583), float(height * 0.264583)
        pdf_size = {'P': {'w': 200, 'h': 287}, 'L': {'w': 287, 'h': 200}}
        width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
        height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']
        self.pdf.image(input_path,5,5,width,height)

    def change_format(self,a,b,c):
        self.edit_settings("Conver to", self.filetype_selected_value.get())

    def load_settings(self):
        settings = open("settings", 'r', encoding='utf-8')
        lines = settings.readlines()
        settings.close()

        for line in lines:
            line = line.replace("\n", "")
            line = line.strip()
            line = line.split(">")
            key = line[0].strip()
            val = line[1].strip()
            self.settings[key] = val
        
        # make sure all settings are there
        requiered_settings = ["Destination", "Conver to"]
        for rs in requiered_settings:
            if not rs in self.settings:
                self.error("Missing setting: \""+rs+"\" edit settings")

    def edit_settings(self, key, val):
        self.settings[key] = val
        settings = open("settings", 'w', encoding='utf-8')
        for key, val in self.settings.items():
            settings.write(key+" > "+val+"\n")
        settings.close()

    def select_folder(self):
        directoy = filedialog.askdirectory(title="Select destination location")
        self.destination_location.delete(0, END)
        self.destination_location.insert(END, directoy)
        self.edit_settings("Destination", directoy)
    
    def change_dst_loc(self, a, b, c):
        directoy = self.destination_location.get()
        self.edit_settings("Destination", directoy)
    
    def delete_item(self, event):
        widget = event.widget
        selection = widget.curselection()
        if len(selection) > 0:
            self.selected_files_list.delete(selection[0],selection[-1])
            self.selected_files_list.selection_clear(0, END)
    
    def error(self, text):
        messagebox.showerror("Error", text)
        sys.exit()
    
    def open_folder(self, path):
        FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        cmd = os.path.normpath(path)
        subprocess.run([FILEBROWSER_PATH, cmd])
    
    def help(self):
        os.popen("help.pdf")

    def today(self):
        # get today
        now = datetime.datetime.now()
        yyyy = str(now.year)
        mm = str(now.month).zfill(2)
        dd = str(now.day).zfill(2)
        return yyyy+"-"+mm+"-"+dd

    def reset(self):
        self.pdf = FPDF()
        self.merger = PdfMerger()
        self.origin_path = ""
        self.destination_path = ""
        self.combine_img_to_pdf = False
        self.combine_pdf_to_pdf = False
        self.index = 1
    
    def get_unique_name(self, file_name):
        # Split the file name into the base name and extension
        base_name, extension = os.path.splitext(file_name)
        
        # Check if the file exists
        counter = 1
        new_name = file_name
        
        while os.path.exists(new_name):
            # Add a number to the file name
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return new_name

image_converer()