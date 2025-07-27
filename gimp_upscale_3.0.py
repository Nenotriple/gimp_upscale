#!/usr/bin/env python3
"""
GIMP AI Upscale Plugin v1.04-test (Gimp 3.0)
Author: github.com/Nenotriple
Upscale directly within GIMP using realesrgan-ncnn-vulkan.

This is a working test for proof-of-concept purposes.
"""


import sys
import os
import tempfile
import subprocess
import gi #type:ignore
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, GimpUi, Gegl, GObject, GLib, Gio #type:ignore


def _txt(message):
    """Translate the given message using GLib's dgettext for localization."""
    return GLib.dgettext(None, message)


# Config constants
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RESRGAN_PATH = os.path.join(SCRIPT_DIR, "resrgan", "realesrgan-ncnn-vulkan.exe")
DEFAULT_MODEL = "realesr-animevideov3-x4"
DEFAULT_OUTPUT_FACTOR = 1.0


def _export_drawable_to_temp(drawable):
    """Export drawable to temporary PNG file"""
    temp_file = tempfile.mktemp(suffix=".png")
    # Export the image using GIMP 3.0 file export
    image = drawable.get_image()
    file = Gio.File.new_for_path(temp_file)
    # Get the export procedure and create its config
    pdb = Gimp.get_pdb()
    procedure = pdb.lookup_procedure('file-png-export')
    config = procedure.create_config()
    # Set the config properties
    config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
    config.set_property('image', image)
    config.set_property('file', file)
    # Run the procedure with the config
    result = procedure.run(config)
    return temp_file


def _run_resrgan(temp_input, temp_output, model):
    """Run Real-ESRGAN upscaling process"""
    try:
        process = subprocess.Popen([RESRGAN_PATH, "-i", temp_input, "-o", temp_output, "-n", model], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Real-ESRGAN failed: {stderr.decode()}")
    except Exception as e:
        raise Exception(f"Error running Real-ESRGAN: {str(e)}")


def _handle_upscaled_layer(image, upscaled_layer, output_factor):
    """Handle the upscaled layer by resizing image and layer appropriately"""
    orig_width = image.get_width()
    orig_height = image.get_height()
    final_width = int(orig_width * output_factor)
    final_height = int(orig_height * output_factor)
    # Resize the image canvas to the final desired size
    image.resize(final_width, final_height, 0, 0)
    # Create a new layer in the target image with the final desired size
    if image.get_base_type() == Gimp.ImageBaseType.RGB:
        layer_type = Gimp.ImageType.RGBA_IMAGE
    else:
        layer_type = Gimp.ImageType.GRAYA_IMAGE
    # Create new layer with final dimensions
    new_layer = Gimp.Layer.new(image, "AI Upscaled Layer", final_width, final_height, layer_type, 100.0, Gimp.LayerMode.NORMAL)
    # Insert the new layer into the target image
    image.insert_layer(new_layer, None, -1)
    # First, scale the upscaled layer to the final desired size
    # The AI upscaler produces 4x, but we want output_factor size
    upscaled_layer.scale(final_width, final_height, False)
    # Copy the pixel data from the scaled upscaled layer to the new layer
    upscaled_buffer = upscaled_layer.get_buffer()
    new_buffer = new_layer.get_buffer()
    # Copy the buffer data with final dimensions
    upscaled_buffer.copy(Gegl.Rectangle.new(0, 0, final_width, final_height), Gegl.AbyssPolicy.NONE, new_buffer, Gegl.Rectangle.new(0, 0, final_width, final_height))
    # Update the layer
    new_layer.update(0, 0, final_width, final_height)
    return new_layer


def ai_upscale(procedure, run_mode, image, drawables, config, data):
    """Main upscaling function"""
    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('python-fu-ai-upscale')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        else:
            dialog.destroy()
    # Get configuration parameters
    model = config.get_property('model')
    output_factor = config.get_property('output_factor')
    Gimp.context_push()
    image.undo_group_start()
    try:
        # Process each drawable
        for drawable in drawables:
            Gimp.progress_set_text("Exporting image...")
            temp_input = _export_drawable_to_temp(drawable)
            temp_output = tempfile.mktemp(suffix=".png")
            Gimp.progress_set_text("AI Upscaling in progress...")
            _run_resrgan(temp_input, temp_output, model)
            Gimp.progress_set_text("Loading upscaled image...")
            # Load the upscaled image using PDB with proper config
            pdb = Gimp.get_pdb()
            load_procedure = pdb.lookup_procedure('file-png-load')
            load_config = load_procedure.create_config()
            # Set the config properties
            load_config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
            load_config.set_property('file', Gio.File.new_for_path(temp_output))
            # Run the procedure with the config
            result = load_procedure.run(load_config)
            upscaled_image = result.index(1)  # Get the image from result
            upscaled_layers = upscaled_image.get_layers()  # Get layers using GIMP 3.0 method
            upscaled_layer = upscaled_layers[0]  # Get first layer
            Gimp.progress_set_text("Processing upscaled layer...")
            _handle_upscaled_layer(image, upscaled_layer, output_factor)
            # Clean up
            upscaled_image.delete()
            os.remove(temp_input)
            os.remove(temp_output)
        Gimp.displays_flush()
        Gimp.progress_set_text("AI Upscaling complete!")
    except Exception as e:
        error = GLib.Error()
        error.message = f"Upscaling failed: {str(e)}"
        return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, error)
    finally:
        image.undo_group_end()
        Gimp.context_pop()
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class AIUpscale(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None


    def do_query_procedures(self):
        return ['python-fu-ai-upscale']


    def do_create_procedure(self, name):
        Gegl.init(None)
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, ai_upscale, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
        procedure.set_documentation(_txt("AI-powered image upscaling"), _txt("Upscale images using Real-ESRGAN AI models"), name)
        procedure.set_menu_label(_txt("AI _Upscale..."))
        procedure.set_attribution("github.com/Nenotriple", "github.com/Nenotriple", "2025")
        procedure.add_menu_path("<Image>/Filters/Enhance")
        # Add model selection parameter
        procedure.add_string_argument("model", _txt("AI _Model"), _txt("AI Model to use for upscaling"), DEFAULT_MODEL, GObject.ParamFlags.READWRITE)
        # Add output factor parameter
        procedure.add_double_argument("output_factor", _txt("Output _Factor"), _txt("Output scaling factor"), 0.05, 8.0, DEFAULT_OUTPUT_FACTOR, GObject.ParamFlags.READWRITE)
        return procedure

Gimp.main(AIUpscale.__gtype__, sys.argv)
