# Download SmartConsole.py from: https://github.com/VladFeldfix/Smart-Console/blob/main/SmartConsole.py
from SmartConsole import *
from PIL import Image
import os

class main:
    # constructor
    def __init__(self):
        # load smart console
        self.sc = SmartConsole("Image Converter", "1.0")

        # set-up main memu
        self.sc.add_main_menu_item("RUN", self.run)

        # get settings
        self.src = self.sc.get_setting("Origin")
        self.dst = self.sc.get_setting("Destination")

        # test all paths
        self.sc.test_path(self.src)
        self.sc.test_path(self.dst)

        # display main menu
        self.sc.start()

    def convert(self, input_path, output_path, scr_format, dst_format):
        try:
            # Open the JFIF image
            with Image.open(input_path) as img:
                # Ensure the format is JFIF
                self.sc.print("The detected format of filename:\n"+input_path+" is "+img.format)
                if img.format == scr_format:
                    # Save the image as JPG
                    img.save(output_path, dst_format)
                    self.sc.good(f"Converted {input_path} to \n{output_path}")
                else:
                    self.sc.error("The file is not in "+scr_format+" format.")
        except Exception as e:
            self.sc.error(f"Error: {e}")
    
    def run(self):
        scr_format = self.sc.input("What is the original format?")
        scr_format = scr_format
        dst_format = self.sc.input("What is the format you want to convert to?")
        dst_format = dst_format

        for root, dirs, files in os.walk(self.src):
            for file in files:
                input_file = self.src+"/"+file  # Input JFIF file
                new_name = self.dst+"/"+file
                new_name = new_name.split(".")
                new_name = new_name[:-1]
                new_name = ".".join(new_name)
                new_name = new_name+"."+dst_format
                output_file = new_name  # Desired output JPG file
                self.convert(input_file, output_file, scr_format, dst_format)
        
        self.sc.open_folder(self.dst)
        
        # restart
        self.sc.restart()

main()
