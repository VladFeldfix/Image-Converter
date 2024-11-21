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

class image_converer:
    def __init__(self):
        self.origin_path = ""
        self.destination_path = ""
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
        root.title("Image Converer v2.1")
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
        options_list = ["jpeg", "png", "bmp", "tiff"]
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
            output_path = self.settings["Destination"]+"/"+filename+"."+self.settings["Conver to"]
            data = self.try_convert(input_path, output_path, self.settings["Conver to"])
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

    def try_convert(self, input_path, output_path, dst_format):
        return_text = ""

        # for images
        try:
            # Open the image
            with Image.open(input_path) as img:
                # Save the image
                img.save(output_path, dst_format)
                return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
        except Exception as e:
            return_text = (input_path+" Error: "+str(e), "BAD")
        
        # for pdf's
        try:
            poppler_path = r"poppler-24.08.0/Library/bin"
            images = convert_from_path(input_path,poppler_path = poppler_path)

            for i, image in enumerate(images):
                image.save(output_path, dst_format)
                return_text = ("Converted: "+input_path+" to "+output_path,"GOOD")
        except Exception as e:
            return_text = (input_path+" Error: "+str(e), "BAD")
        return return_text
    
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

image_converer()