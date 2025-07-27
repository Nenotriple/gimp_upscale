#!/usr/bin/env python

"""
GIMP AI Upscale Plugin v1.04 (Gimp 2.10)
Author: github.com/Nenotriple
Upscale directly within GIMP using realesrgan-ncnn-vulkan.
"""

import os
import tempfile
import subprocess

from gimpfu import main, register, pdb, PF_IMAGE, PF_DRAWABLE

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RESRGAN_PATH = os.path.join(SCRIPT_DIR, "resrgan/realesrgan-ncnn-vulkan.exe")
MODEL = "realesr-animevideov3-x4"
OUTPUT_FACTOR = 1.0


def _export_image_to_temp(image, drawable):
    temp_file = tempfile.mktemp(suffix=".png")
    pdb.file_png_save_defaults(image, drawable, temp_file, temp_file)
    return temp_file


def _run_resrgan(temp_input, temp_output):
    pdb.gimp_progress_set_text("Upscaling...")
    subprocess.call([RESRGAN_PATH, "-i", temp_input, "-o", temp_output, "-n", MODEL], shell=True)


def _handle_upscaled_layer(image, upscaled_layer, output_factor):
    orig_width, orig_height = pdb.gimp_image_width(image), pdb.gimp_image_height(image)
    output_width, output_height = int(orig_width * output_factor), int(orig_height * output_factor)
    pdb.gimp_image_resize(image, output_width, output_height, 0, 0)
    pdb.gimp_layer_scale(upscaled_layer, output_width, output_height, False)
    upscaled_layer_resized = pdb.gimp_layer_new_from_drawable(upscaled_layer, image)
    pdb.gimp_image_insert_layer(image, upscaled_layer_resized, None, -1)


def execute_upscale_process(image, drawable):
    pdb.gimp_image_undo_group_start(image)
    try:
        temp_input = _export_image_to_temp(image, drawable)
        temp_output = tempfile.mktemp(suffix=".png")
        _run_resrgan(temp_input, temp_output)
        upscaled_image = pdb.gimp_file_load(temp_output, temp_output)
        upscaled_layer = pdb.gimp_image_get_active_layer(upscaled_image)
        _handle_upscaled_layer(image, upscaled_layer, OUTPUT_FACTOR)
        pdb.gimp_image_delete(upscaled_image)
        os.remove(temp_input)
        os.remove(temp_output)
        pdb.gimp_displays_flush()
    finally:
        pdb.gimp_image_undo_group_end(image)


register(
    proc_name="python-fu-upscale-with-ncnn",
    blurb="Upscale using AI models",
    help="AI-powered image upscaling using realesrgan-ncnn-vulkan",
    author="github.com/Nenotriple",
    copyright="MIT License 2025",
    date="2025",
    label="AI Upscale",
    menu="<Image>/Filters",
    imagetypes="*",
    params=[
        (PF_IMAGE, "image", "Input Image", None),
        (PF_DRAWABLE, "drawable", "Input Drawable", None),
    ],
    results=[],
    function=execute_upscale_process,
)

main()
