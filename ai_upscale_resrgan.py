"""
########################################
#             gimp_upscale             #
#   Version : v1.01                    #
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
import subprocess

# GIMP Library
from gimpfu import *


# --------------------------------------
# Update the list of available models
# --------------------------------------

def find_additional_models():
    '''Function to find additional upscale models in the "resrgan/models" folder'''
    script_dir = os.path.dirname(os.path.realpath(__file__))
    models_dir = os.path.join(script_dir, "resrgan/models")
    # List all files in the models directory
    all_files = os.listdir(models_dir)
    # Filter out .bin and .param files
    bin_files = {os.path.splitext(f)[0] for f in all_files if f.endswith('.bin')}
    param_files = {os.path.splitext(f)[0] for f in all_files if f.endswith('.param')}
    # Find paired models
    paired_models = bin_files & param_files
    # Hardcoded models to ignore
    hardcoded_models = {
        "realesr-animevideov3-x2",
        "realesr-animevideov3-x3",
        "realesr-animevideov3-x4",
        "RealESRGAN_General_x4_v3",
        "realesrgan-x4plus",
        "realesrgan-x4plus-anime",
        "UltraSharp-4x",
        "AnimeSharp-4x"
        }
    # Exclude hardcoded models
    additional_models = [model for model in paired_models if model not in hardcoded_models]
    return additional_models


# --------------------------------------
# List of available models
# --------------------------------------


# Hardcoded model list
HARDCODED_MODELS = [
    "realesr-animevideov3-x4",
    "RealESRGAN_General_x4_v3",
    "realesrgan-x4plus",
    "realesrgan-x4plus-anime",
    "UltraSharp-4x",
    "AnimeSharp-4x"
    ]


# Available models
MODELS = HARDCODED_MODELS + find_additional_models()


# --------------------------------------
# Functions
# --------------------------------------


def export_image_to_temp(image, drawable):
    '''Function to export the current image to a temporary file'''
    temp_input_file = tempfile.mktemp(suffix=".png")
    pdb.file_png_save_defaults(image, drawable, temp_input_file, temp_input_file)
    return temp_input_file


def run_resrgan(temp_input_file, temp_output_file, model):
    '''Upscale the image using the RESRGAN executable'''
    script_dir = os.path.dirname(os.path.realpath(__file__))
    resrgan_exe = os.path.join(script_dir, "resrgan/realesrgan-ncnn-vulkan.exe")
    # Run the RESRGAN command
    upscale_process = subprocess.Popen([
        resrgan_exe,
        "-i", temp_input_file,
        "-o", temp_output_file,
        "-n", model
        ])
    upscale_process.wait()


def load_upscaled_image(image, drawable, temp_output_file, output_factor, upscale_selection):
    '''Function to load the upscaled image back into GIMP'''
    upscaled_image = pdb.gimp_file_load(temp_output_file, temp_output_file)
    upscaled_layer = pdb.gimp_image_get_active_layer(upscaled_image)
    if upscale_selection:
        # Get the position of the original selection
        x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)[1:]
        # Calculate the selection dimensions
        sel_width = x2 - x1
        sel_height = y2 - y1
        # Resize the upscaled layer to match the selection dimensions
        pdb.gimp_layer_scale(upscaled_layer, sel_width, sel_height, False)
        # Create a new transparent layer with the size of the input layer
        new_layer = pdb.gimp_layer_new(image, pdb.gimp_drawable_width(drawable),
                                       pdb.gimp_drawable_height(drawable), RGBA_IMAGE,
                                       "Upscaled Selection", 100, NORMAL_MODE)
        pdb.gimp_image_insert_layer(image, new_layer, None, -1)
        # Copy the upscaled content to the new layer at the original selection position
        pdb.gimp_edit_copy(upscaled_layer)
        floating_sel = pdb.gimp_edit_paste(new_layer, False)
        pdb.gimp_layer_set_offsets(floating_sel, x1, y1)
        pdb.gimp_floating_sel_anchor(floating_sel)
    else:
        # Get dimensions of the original image
        orig_width = pdb.gimp_image_width(image)
        orig_height = pdb.gimp_image_height(image)
        # Calculate the output size based on the user-specified factor
        output_width = int(orig_width * output_factor)
        output_height = int(orig_height * output_factor)
        # Resize the image canvas to match the calculated output size
        pdb.gimp_image_resize(image, output_width, output_height, 0, 0)
        # Scale the upscaled image to the calculated output size
        pdb.gimp_layer_scale(upscaled_layer, output_width, output_height, False)
        # Create a new layer from the upscaled drawable
        upscaled_layer_resized = pdb.gimp_layer_new_from_drawable(upscaled_layer, image)
        pdb.gimp_image_insert_layer(image, upscaled_layer_resized, None, -1)
    # Remove the temporary upscaled image (not the layer)
    pdb.gimp_image_delete(upscaled_image)


def upscale_with_ncnn(image, drawable, model_index, output_factor, upscale_selection):
    '''Main function to upscale the image using realesrgan-ncnn-vulkan.exe'''
    pdb.gimp_image_undo_group_start(image)
    try:
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
        # Export the selected content to a temporary file
        temp_input_file = export_image_to_temp(image, selected_layer)
        temp_output_file = tempfile.mktemp(suffix=".png")
        # Run the RESRGAN upscaling process (no scaling argument used)
        model = MODELS[model_index]
        run_resrgan(temp_input_file, temp_output_file, model)
        # Load the upscaled image back into GIMP
        load_upscaled_image(image,
                            selected_layer,
                            temp_output_file,
                            output_factor,
                            upscale_selection
                            )
        # Clean up temporary files
        os.remove(temp_input_file)
        os.remove(temp_output_file)
        pdb.gimp_displays_flush()
    finally:
        pdb.gimp_image_undo_group_end(image)


# --------------------------------------
# Register the function with GIMP
# --------------------------------------


register(
    "Nenotriple_upscale-with-NCNN",
    "Upscale using NCNN",
    "Upscale using NCNN",
    "github/Nenotriple", "github/Nenotriple/gimp_upscale", "2024",
    "<Image>/Filters/Enhance/AI Upscale (NCNN)...",
    "*",
    [
        # Model selection
        (PF_OPTION, "model_index", "Model", 0, MODELS),
        # Option to upscale only the selected content
        (PF_OPTION, "upscale_selection", "Upscale Input", 0, ["From Layer", "From Selection"]),
        # Output size factor
        (PF_SPINNER, "output_factor", "Output Size Factor", 1.0, (1.00, 4.00, 0.01))
    ],
    [],
    upscale_with_ncnn)


main()
