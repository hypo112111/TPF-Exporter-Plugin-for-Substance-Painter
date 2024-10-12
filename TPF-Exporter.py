__author__ = "Emil Eldstål"
__modified_by__ = "hypo112111"
__copyright__ = "Copyright 2023, Emil Eldstål"
__version__ = "0.1.1"


from PySide6 import QtWidgets
from PySide6.QtCore import Qt

import substance_painter.ui
import substance_painter.event

import xml.etree.ElementTree as ET

import os
import configparser
import subprocess

def config_ini(overwrite):
    # Get the path to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the path to the StarfieldPluginSettings.ini file
    ini_file_path = os.path.join(script_dir, "TPF-Exporter-PluginSettings.ini")            
    
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Check if the INI file exists
    if os.path.exists(ini_file_path):
        # Read the INI file
        config.read(ini_file_path)
        
        # Check if the section and key exist
        if 'General' in config and 'TexConvDirectory' in config['General']:
            # Check if the value is empty
            if not config['General']['TexConvDirectory']:
                # Let's the user choose where TexConv is if not configured
                config['General']['TexConvDirectory'] = choose_texconv_folder()
            if overwrite:
                # Let's the user choose where TexConv is if using overwrite button
                config['General']['TexConvDirectory'] = choose_texconv_folder()

            # Assign the TexConvDirectory value to the TexConvPath variable
            TexConvPath = config['General']['TexConvDirectory']
        else:
            TexConvPath = choose_texconv_folder()
            # If the section or key doesn't exist, create it and set the value
            config['General'] = {}
            config['General']['TexConvDirectory'] = TexConvPath
            print("TPF Exporter Plugin: TexConvDirectory value set or updated in TPFPluginSettings.ini")

        # Check if the Yabber section and key exist
        if 'General' in config and 'YabberDirectory' in config['General']:
            # Check if the value is empty
            if not config['General']['YabberDirectory']:
                # Let's the user choose where TexConv is if not configured
                config['General']['YabberDirectory'] = choose_yabber_folder()
            if overwrite:
                # Let's the user choose where TexConv is if using overwrite button
                config['General']['YabberDirectory'] = choose_yabber_folder()

            # Assign the TexConvDirectory value to the TexConvPath variable
            YabberPath = config['General']['YabberDirectory']
        else:
            YabberPath = choose_yabber_folder()
            # If the section or key doesn't exist, create it and set the value
            config['General'] = {}
            config['General']['YabberDirectory'] = YabberPath
            print("TPF Exporter Plugin: YabberDirectory value set or updated in TPFPluginSettings.ini")

        # Write the updated configuration back to the INI file
        with open(ini_file_path, 'w') as configfile:
            config.write(configfile)
    else:
        TexConvPath = choose_texconv_folder()
        YabberPath = choose_yabber_folder()
        # If the INI file doesn't exist, create it and set the value
        with open(ini_file_path, 'w') as configfile:
            config['General'] = {}
            config['General']['TexConvDirectory'] = TexConvPath
            config['General']['YabberDirectory'] = YabberPath
            config.write(configfile)

    configPath = {
        "texConvPath" : TexConvPath,
        "yabberPath" : YabberPath
    }
    return configPath

def choose_texconv_folder():
    path = QtWidgets.QFileDialog.getExistingDirectory(
    substance_painter.ui.get_main_window(),"Choose Texconv directory")
    return path +"/texconv.exe"

def choose_yabber_folder():
    path = QtWidgets.QFileDialog.getExistingDirectory(
    substance_painter.ui.get_main_window(),"Choose yabber directory")
    return path +"/yabber.exe"

def convert_png_to_dds(texconvPath, sourcePNG):
    # Replace backslashes with forward slashes in the provided paths
    texconvPath = texconvPath.replace('\\', '/')
    sourceFolder = os.path.dirname(sourcePNG)
    sourceFolder = sourceFolder.replace('\\', '/')
    outputFolder = sourceFolder + "/DDS/"

    isExist = os.path.exists(outputFolder)
    if not isExist:
        # Create the DDS directory if it does not exist
        os.makedirs(outputFolder)
        print("Created DDS subfolder")

    # for filename in os.listdir(sourceFolder):
    filename = sourcePNG
    if filename.endswith(".png"):
        sourceFile = os.path.splitext(filename)[0]
        suffix = sourceFile.split('_')[-1]
        suffix = suffix.rstrip('_')

        outputFile = None

        # This is the suffix used for Metallic (Replace with other suffix for other game)
        if suffix in ["1m", "3m"] or suffix in ["Metallic", "Roughness"]:
            outputFile = sourceFile + ".dds"
            format_option = "BC4_UNORM"
        # This is the suffix used for Normal (Replace with other suffix for other game)
        elif suffix == "n" or suffix == "Normal":
            outputFile = sourceFile + ".dds"
            format_option = "BC5_SNORM"
        # This is the suffix used for BaseColor (Replace with other suffix for other game)
        elif suffix == "a" or suffix == "BaseColor":
            outputFile = sourceFile + ".dds"
            format_option = "BC7_UNORM"
        
        # No support for alpha

        format_option = format_option.rstrip('"')
        if outputFile:
            texconv_cmd = [
                texconvPath,
                "-nologo",
                "-o", outputFolder,
                "-f", format_option,
                os.path.join(sourceFolder, filename)
            ]

            texconv_cmd_str = subprocess.list2cmdline(texconv_cmd)

            try:
                subprocess.run(texconv_cmd_str, shell=True, check=True)
                print(f"Successfully converted {filename} to {outputFile}")
            except subprocess.CalledProcessError:
                print(f"Failed to convert {filename}")

def create_tpf(YabberPath,sourcePNG):

    # Replace backslashes with forward slashes in the provided paths
    YabberPath = YabberPath.replace('\\', '/')
    sourceFolder = os.path.dirname(sourcePNG)
    sourceFolder = sourceFolder.replace('\\', '/')
    folder = sourceFolder + "/DDS"

    yabber_cmd = [
        YabberPath,
        folder
    ]
    
    try:
        subprocess.run(yabber_cmd, capture_output=True, text=True, check=True)
        print(f"Successfully repacked {folder}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to repack {folder}")
        print(f"Command failed with return code {e.returncode}")
        print(f"Command: {e.cmd}")

def make_yabber_tpf_xml(file_path):

    # Replace backslashes with forward slashes in the provided paths
    file_path = file_path.replace('\\', '/')
    sourceFolder = os.path.dirname(file_path)
    sourceFolder = sourceFolder.replace('\\', '/')
    folder = sourceFolder + "/DDS"

    # XML root
    tpf = ET.Element("tpf")

    # Construct the XML Structure
    filename = ET.SubElement(tpf, "filename")
    filename.text = folder[0:-4].rsplit("/", 1)[1] + ".tpf"

    compression = ET.SubElement(tpf, "compression")
    compression.text = "None"

    encoding = ET.SubElement(tpf, "encoding")
    encoding.text = "0x01"

    flag2 = ET.SubElement(tpf, "flag2")
    flag2.text = "0x03"

    textures = ET.SubElement(tpf, "textures")

    images = os.listdir(folder)
    if "_yabber-tpf.xml" in images:
        images.pop(images.index("_yabber-tpf.xml"))

    for image in images:

        texture = ET.SubElement(textures, "texture")
        
        name = ET.SubElement(texture, "name")
        name.text = image
    
        format = ET.SubElement(texture, "format")
        format.text = "0x00"
    
        flags1 = ET.SubElement(texture, "flags1")
        flags1.text = "0x00"
    
        flags2 = ET.SubElement(texture, "flags2")
        flags2.text = "0x00000000"
    
    # XML object
    xml = ET.ElementTree(tpf)

    # Make sure _yabber-tpf.xml itself does not get repacked
    xml_file = os.path.join(folder, "_yabber-tpf.xml")

    # XML to file
    with open(xml_file, "wb") as files:
        xml.write(files, encoding="utf-8", xml_declaration=True)

class TPFExportPlugin:
    def __init__(self):
        # Export boolean whether to add DDS creation or not
        self.export = True
        
        self.version = 0.2

        self.ddsexport = True

        # Create a dock widget to report plugin activity.
        self.log = QtWidgets.QTextEdit()
        self.window = QtWidgets.QWidget()
        self.configPath = config_ini(False)

        layout = QtWidgets.QVBoxLayout()
        sub_layout = QtWidgets.QHBoxLayout()

        checkbox = QtWidgets.QCheckBox("Export")
        checkbox.setChecked(True)
        button_config = QtWidgets.QPushButton("Choose Config Path")
        button_clear = QtWidgets.QPushButton("Clear Log")
        version_label = QtWidgets.QLabel("Version: {}".format(self.version))

        # Adds buttons to sub-layout
        sub_layout.addWidget(checkbox)
        sub_layout.addWidget(button_config)
        sub_layout.addWidget(button_clear)

        # Adds all widgets to main layout
        layout.addLayout(sub_layout)
        layout.addWidget(self.log)
        layout.addWidget(version_label)

        self.window.setLayout(layout)
        self.window.setWindowTitle("TPF Exporter")
        self.log.setReadOnly(True)

        # Connects buttons to click events
        checkbox.stateChanged.connect(self.checkbox_export_change)
        button_config.clicked.connect(self.button_config_clicked)
        button_clear.clicked.connect(self.button_clear_clicked)

        # Adds Qt as dockable widget to Substance Painter
        substance_painter.ui.add_dock_widget(self.window)

        self.log.append("TexConv Path: {}".format(self.configPath["texConvPath"]))
        self.log.append("Yabber Path: {}".format(self.configPath["yabberPath"]))

        connections = {
            substance_painter.event.ExportTexturesEnded: self.on_export_finished
        }
        for event, callback in connections.items():
            substance_painter.event.DISPATCHER.connect(event, callback)

    def button_config_clicked(self):
        self.configPath = config_ini(True)
        self.log.append("New TexConv Path: {}".format(self.configPath["texConvPath"]))
        self.log.append("New Yabber Path: {}".format(self.configPath["yabberPath"]))

    def button_clear_clicked(self):
        self.log.clear()

    def checkbox_export_change(self,state):
        if state == Qt.Checked:
            self.ddsexport = True
        else:
            self.ddsexport = False

    def __del__(self):
        # Remove all added UI elements.
        substance_painter.ui.delete_ui_element(self.log)
        substance_painter.ui.delete_ui_element(self.window)

    def on_export_finished(self, res):
        if(self.export):
            self.log.append(res.message)
            self.log.append("Exported files:")
            for file_list in res.textures.values():
                for file_path in file_list:
                    self.log.append("  {}".format(file_path))
                    
            self.log.append("Converting to DDS files:")
            for file_list in res.textures.values():
                for file_path in file_list:
                    convert_png_to_dds(self.configPath["texConvPath"],file_path)
                    file_path = file_path[:-3]+"DDS"
                    self.log.append("  {}".format(file_path))
                    
            self.log.append("Creating TPF file:")
            for file_list in res.textures.values():
                for file_path in file_list:

                    # make _yabber-tpf.xml for the yabber.exe
                    make_yabber_tpf_xml(file_path)
                    self.log.append("Successfully created _yabber-tpf.xml")

                    #Repack tpf
                    create_tpf(self.configPath["yabberPath"],file_path)
                    self.log.append("Successfully repacked")
                    break
                break

    def on_export_error(self, err):
        self.log.append("Export failed.")
        self.log.append(repr(err))

TPF_Export_PLUGIN = None

def start_plugin():
    """This method is called when the plugin is started."""
    print ("TPF Exporter Plugin Initialized")
    global TPF_Export_PLUGIN
    TPF_Export_PLUGIN = TPFExportPlugin()

def close_plugin():
    """This method is called when the plugin is stopped."""
    print ("TPF Exporter Plugin Shutdown")
    global TPF_Export_PLUGIN
    del TPF_Export_PLUGIN

if __name__ == "__main__":
    start_plugin()