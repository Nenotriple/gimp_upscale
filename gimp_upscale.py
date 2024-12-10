#!/usr/bin/env python


"""
########################################
#             gimp_upscale             #
#   Version : v1.03                    #
#   Author  : github.com/Nenotriple    #
########################################

Description:
-------------
Upscale directly within GIMP using ESRGAN/NCNN models.

More info here: https://github.com/Nenotriple/gimp_upscale

"""


# --------------------------------------
# Imports
# --------------------------------------


# Standard Library
import os
import tempfile
import platform
import subprocess


# GIMP Library
from gimpfu import main, register, pdb, RGBA_IMAGE, NORMAL_MODE, PF_OPTION, PF_TOGGLE, PF_SPINNER, PF_IMAGE, PF_DRAWABLE  # type: ignore


# --------------------------------------
# Global Variables
# --------------------------------------


# Directory of the script
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


# Directory of the models
MODEL_DIR = os.path.join(SCRIPT_DIR, "resrgan/models")


# Predefined model list
HARDCODED_MODELS = [
    "realesr-animevideov3-x4",
    "RealESRGAN_General_x4_v3",
    "realesrgan-x4plus",
    "realesrgan-x4plus-anime",
    "UltraSharp-4x",
    "AnimeSharp-4x"
]


# --------------------------------------
# Update the list of available models
# --------------------------------------


def _find_additional_models():
    '''Function to find additional upscale models in the "resrgan/models" folder'''
    # List all files in the models directory
    all_files = os.listdir(MODEL_DIR)
    # Filter out .bin and .param files
    bin_files = {os.path.splitext(f)[0] for f in all_files if f.endswith('.bin')}
    param_files = {os.path.splitext(f)[0] for f in all_files if f.endswith('.param')}
    # Find paired models
    paired_models = bin_files & param_files
    # Filter out hardcoded models
    models = [model for model in paired_models if model not in HARDCODED_MODELS]
    return models


# Combine predefined models with additional discovered models
MODELS = HARDCODED_MODELS + _find_additional_models()


# --------------------------------------
# Functions
# --------------------------------------


def _get_layer_or_selection(image, drawable, upscale_selection):
    '''Retrieves the active layer or creates a new one from the selection.'''
    if upscale_selection and pdb.gimp_selection_is_empty(image):
        pdb.gimp_message("Please make a selection first.")
        return
    if upscale_selection:
        # Create a new layer from the selection
        pdb.gimp_edit_copy(drawable)
        floating_sel = pdb.gimp_edit_paste(image.active_layer, True)
        pdb.gimp_floating_sel_to_layer(floating_sel)
        selected_layer = pdb.gimp_image_get_active_layer(image)
    else:
        selected_layer = drawable
    return selected_layer


def _export_image_to_temp(image, drawable):
    '''Exports the selected layer to a temporary file.'''
    temp_input_file = tempfile.mktemp(suffix=".png")
    pdb.file_png_save_defaults(image, drawable, temp_input_file, temp_input_file)
    return temp_input_file


def _run_resrgan(temp_input_file, temp_output_file, model):
    '''Upscale the image using the RESRGAN executable'''
    if platform.system() == "Windows":
        resrgan_exe = os.path.join(SCRIPT_DIR, "resrgan/realesrgan-ncnn-vulkan.exe")
    else:  # Linux
        resrgan_exe = os.path.join(SCRIPT_DIR, "resrgan/realesrgan-ncnn-vulkan")
        # Make sure the executable has the correct permissions
        subprocess.call(['chmod', 'u+x', resrgan_exe])
    upscale_process = subprocess.Popen([
        resrgan_exe,
        "-i", temp_input_file,
        "-o", temp_output_file,
        "-n", model
    ])
    upscale_process.wait()


def _load_upscaled_image(image, drawable, temp_output_file, output_factor, upscale_selection):
    '''Loads the upscaled image back into GIMP in a new layer'''
    upscaled_image = pdb.gimp_file_load(temp_output_file, temp_output_file)
    upscaled_layer = pdb.gimp_image_get_active_layer(upscaled_image)
    if upscale_selection:
        _handle_upscaled_selection(image, drawable, upscaled_layer)
    else:
        _handle_upscaled_layer(image, drawable, upscaled_layer, output_factor)
    # Clean up the temporary upscaled image
    pdb.gimp_image_delete(upscaled_image)


def _handle_upscaled_selection(image, drawable, upscaled_layer):
    '''Handles the upscaled image when upscaling a selection'''
    x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)[1:]
    sel_width = x2 - x1
    sel_height = y2 - y1
    pdb.gimp_layer_scale(upscaled_layer, sel_width, sel_height, False)
    new_layer = pdb.gimp_layer_new(image, pdb.gimp_drawable_width(drawable), pdb.gimp_drawable_height(drawable), RGBA_IMAGE, "Upscaled Selection", 100, NORMAL_MODE)
    pdb.gimp_image_insert_layer(image, new_layer, None, -1)
    pdb.gimp_edit_copy(upscaled_layer)
    floating_sel = pdb.gimp_edit_paste(new_layer, False)
    pdb.gimp_layer_set_offsets(floating_sel, x1, y1)
    pdb.gimp_floating_sel_anchor(floating_sel)


def _handle_upscaled_layer(image, drawable, upscaled_layer, output_factor):
    '''Handles the upscaled image when upscaling a layer'''
    orig_width = pdb.gimp_image_width(image)
    orig_height = pdb.gimp_image_height(image)
    output_width = int(orig_width * output_factor)
    output_height = int(orig_height * output_factor)
    pdb.gimp_image_resize(image, output_width, output_height, 0, 0)
    pdb.gimp_layer_scale(upscaled_layer, output_width, output_height, False)
    upscaled_layer_resized = pdb.gimp_layer_new_from_drawable(upscaled_layer, image)
    pdb.gimp_image_insert_layer(image, upscaled_layer_resized, None, -1)


def _cleanup_temp_files(image, selected_layer, temp_input_file, temp_output_file, upscale_selection, keep_copy_layer):
    '''Function to clean up temporary files and layers'''
    os.remove(temp_input_file)
    os.remove(temp_output_file)
    if not keep_copy_layer and upscale_selection:
        pdb.gimp_image_remove_layer(image, selected_layer)
    pdb.gimp_displays_flush()


# --------------------------------------
# Primary Function
# --------------------------------------


def upscale_with_ncnn(image, drawable, model_index, upscale_selection, keep_copy_layer, output_factor):
    '''Main function that orchestrates the upscaling process using realesrgan-ncnn-vulkan.'''
    pdb.gimp_image_undo_group_start(image)
    try:
        # Get the target layer or selection
        selected_layer = _get_layer_or_selection(image, drawable, upscale_selection)
        # Export the target to a temporary file
        temp_input_file = _export_image_to_temp(image, selected_layer)
        temp_output_file = tempfile.mktemp(suffix=".png")
        # Perform the upscaling
        model = MODELS[model_index]
        _run_resrgan(temp_input_file, temp_output_file, model)
        # Load the upscaled image back into GIMP
        _load_upscaled_image(image, selected_layer, temp_output_file, output_factor, upscale_selection)
        # Clean up temporary files and layers
        _cleanup_temp_files(image, selected_layer, temp_input_file, temp_output_file, upscale_selection, keep_copy_layer)
    finally:
        pdb.gimp_image_undo_group_end(image)


# --------------------------------------
# GIMP Plug-in Registration
# --------------------------------------


register(
    proc_name="python-fu-upscale-with-ncnn",
    blurb="Upscale using AI-powered ESRGAN models\t\n---\t\ngithub.com/Nenotriple/gimp_upscale\t",
    help="This plugin provides AI-powered image upscaling using ESRGAN/NCNN models; github.com/Nenotriple/gimp_upscale",
    author="github.com/Nenotriple",
    copyright="github/Nenotriple; MIT-LICENSE; 2024;",
    date="2024",
    label="AI Upscale (NCNN)...",
    menu="<Image>/Filters/Enhance",
    imagetypes="*",
    params=[
        (PF_IMAGE, "image", "Input Image", None),
        (PF_DRAWABLE, "drawable", "Input Drawable", None),
        (PF_OPTION, "model_index", "AI Model", 0, MODELS),
        (PF_OPTION, "upscale_selection", "Input Source", 0, ["Layer", "Selection"]),
        (PF_TOGGLE, "keep_copy_layer", "Keep Selection Copy", False),
        (PF_SPINNER, "output_factor", "Size Factor", 1.0, (1.00, 4.00, 0.01))
    ],
    results=[],
    function=upscale_with_ncnn,
)


main()

