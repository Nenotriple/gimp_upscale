#!/usr/bin/env python


"""
########################################
#             gimp_upscale             #
#   Version : v1.04                    #
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


# Default values:
DEFAULT_MODEL_INDEX = 0
DEFAULT_SELECTION_MODE = 0 # Layer
DEFAULT_KEEP_COPY_LAYER = False
DEFAULT_SCALE_FACTOR = 1.0


# Scale factor range
SCALE_START = 0.1
SCALE_END = 8.0
SCALE_INCREMENT = 0.05


# --------------------------------------
# Get RESRGAN Executable Path
# --------------------------------------
def get_resrgan_executable_path(PLATFORM, SCRIPT_DIR):
    EXECUTABLES = {
        "Windows": "realesrgan-ncnn-vulkan.exe",
        "Linux": "realesrgan-ncnn-vulkan_linux"
    }
    # Check if platform is supported
    if PLATFORM not in EXECUTABLES:
        raise Exception("Unsupported platform")
    # Set platform dependant RESRGAN executable path
    RESRGAN_PATH = os.path.join(SCRIPT_DIR, "resrgan", EXECUTABLES[PLATFORM])
    # Make executable for Unix-like systems
    if PLATFORM == "Linux":
        subprocess.call(['chmod', 'u+x', RESRGAN_PATH])
    return RESRGAN_PATH


# Get the operation System
PLATFORM = platform.system()


# Get platform-specific RESRGAN executable path
RESRGAN_PATH = get_resrgan_executable_path(PLATFORM, SCRIPT_DIR)


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


def _run_resrgan(temp_input_file, temp_output_file, model, shell):
    '''Upscale the image using the RESRGAN executable'''
    upscale_process = subprocess.Popen([
        RESRGAN_PATH,
        "-i", temp_input_file,
        "-o", temp_output_file,
        "-n", model
    ], shell=shell)
    pdb.gimp_progress_set_text("Upscaling...")
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
def execute_upscale_process(image, drawable, model_index, upscale_selection, keep_copy_layer, tiled_upscale, tile_size, output_factor):
    '''Main function that orchestrates the upscaling process using realesrgan-ncnn-vulkan.'''
    pdb.gimp_image_undo_group_start(image)
    try:
        # Get the model and platform specific shell flag
        model = MODELS[model_index]
        shell = True if PLATFORM == "Windows" else False

        if not tiled_upscale:
            # Regular (non-tiled) upscale
            selected_layer = _get_layer_or_selection(image, drawable, upscale_selection)
            temp_input_file = _export_image_to_temp(image, selected_layer)
            temp_output_file = tempfile.mktemp(suffix=".png")
            _run_resrgan(temp_input_file, temp_output_file, model, shell)
            _load_upscaled_image(image, selected_layer, temp_output_file, output_factor, upscale_selection)
            _cleanup_temp_files(image, selected_layer, temp_input_file, temp_output_file, upscale_selection, keep_copy_layer)
        else:
            # Tiled upscale process
            _process_tiles(image, drawable, model, shell, output_factor, tile_size)
    finally:
        pdb.gimp_image_undo_group_end(image)


# --------------------------------------
# Tiled Image Processing
# --------------------------------------
def _process_tiles(image, drawable, model, shell, output_factor, tile_size):
    '''Process image in tiles: crop, upscale and stitch them back.'''
    # Get original dimensions
    orig_width = pdb.gimp_image_width(image)
    orig_height = pdb.gimp_image_height(image)
    new_width = int(orig_width * output_factor)
    new_height = int(orig_height * output_factor)
    # Create a new blank image to stitch upscaled tiles
    stitched_image = pdb.gimp_image_new(new_width, new_height, image.base_type)
    stitched_layer = pdb.gimp_layer_new(stitched_image, new_width, new_height, RGBA_IMAGE, "Upscaled", 100, NORMAL_MODE)
    pdb.gimp_image_insert_layer(stitched_image, stitched_layer, None, -1)
    y = 0
    # Process image in tiles
    while y < orig_height:
        tile_h = min(tile_size, orig_height - y)
        x = 0
        while x < orig_width:
            tile_w = min(tile_size, orig_width - x)
            # Duplicate image and crop to tile region
            tile_image = pdb.gimp_image_duplicate(image)
            pdb.gimp_image_crop(tile_image, tile_w, tile_h, x, y)
            tile_drawable = pdb.gimp_image_get_active_layer(tile_image)
            temp_input = _export_image_to_temp(tile_image, tile_drawable)
            temp_output = tempfile.mktemp(suffix=".png")
            _run_resrgan(temp_input, temp_output, model, shell)
            # Load upscaled tile
            up_tile_img = pdb.gimp_file_load(temp_output, temp_output)
            up_tile_layer = pdb.gimp_image_get_active_layer(up_tile_img)
            # Scale tile as per output factor
            up_tile_w = int(tile_w * output_factor)
            up_tile_h = int(tile_h * output_factor)
            pdb.gimp_layer_scale(up_tile_layer, up_tile_w, up_tile_h, False)
            # Paste upscaled tile into stitched image
            pdb.gimp_edit_copy(up_tile_layer)
            floating_sel = pdb.gimp_edit_paste(stitched_layer, False)
            pdb.gimp_layer_set_offsets(floating_sel, int(x * output_factor), int(y * output_factor))
            pdb.gimp_floating_sel_anchor(floating_sel)
            # Clean up temporary files and images
            os.remove(temp_input)
            os.remove(temp_output)
            pdb.gimp_image_delete(tile_image)
            pdb.gimp_image_delete(up_tile_img)
            x += tile_size
        y += tile_size
    # Display the stitched image
    pdb.gimp_display_new(stitched_image)
    pdb.gimp_displays_flush()


# --------------------------------------
# GIMP Plug-in Registration
# --------------------------------------
register(
    proc_name = "python-fu-upscale-with-ncnn",
    blurb = "v1.04 -- Upscale using Real-ESRGAN\t\n---\t\ngithub.com/Nenotriple/gimp_upscale\t",
    help = "This plugin provides AI-powered image upscaling using ESRGAN/NCNN models; github.com/Nenotriple/gimp_upscale",
    author = "github.com/Nenotriple",
    copyright = "github/Nenotriple; MIT-LICENSE; 2024;",
    date = "2024",
    label = "AI Upscale (NCNN)...",
    menu = "<Image>/Filters/Enhance",
    imagetypes = "*",
    params = [
        (PF_IMAGE, "image", "Input Image", None),
        (PF_DRAWABLE, "drawable", "Input Drawable", None),
        (PF_OPTION, "model_index", "AI Model", DEFAULT_MODEL_INDEX, MODELS),
        (PF_OPTION, "upscale_selection", "Input Source", DEFAULT_SELECTION_MODE, ["Layer", "Selection"]),
        (PF_TOGGLE, "keep_copy_layer", "Keep Selection Copy", DEFAULT_KEEP_COPY_LAYER),
        (PF_TOGGLE, "tiled_upscale", "Tiled Upscale", False),
        (PF_SPINNER, "tile_size", "Tile Size", 768, (128, 1024, 1)),
        (PF_SPINNER, "output_factor", "Size Factor", DEFAULT_SCALE_FACTOR, (SCALE_START, SCALE_END, SCALE_INCREMENT))
    ],
    results = [],
    function = execute_upscale_process,
)


main()