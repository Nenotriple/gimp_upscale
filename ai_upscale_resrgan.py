from gimpfu import *
import subprocess
import os
import tempfile

# Available models
MODELS = ["realesr-animevideov3-x4", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]

def upscale_with_third_party(image, drawable, scale_factor, model_index):
    # Start the undo group
    pdb.gimp_image_undo_group_start(image)  # Group the following steps into a single undo action

    try:
        # Step 1: Export the current image to a temporary file
        temp_input_file = tempfile.mktemp(suffix=".png")
        temp_output_file = tempfile.mktemp(suffix=".png")

        pdb.file_png_save_defaults(image, drawable, temp_input_file, temp_input_file)

        # Step 2: Define the path to the third-party executable relative to the script location
        script_dir = os.path.dirname(os.path.realpath(__file__))
        third_party_exe = os.path.join(script_dir, "resrgan/realesrgan-ncnn-vulkan.exe")

        # Get the model based on the selected index
        model = MODELS[model_index]

        # Step 3: Call the third-party executable to upscale the image by a fixed scale factor of 4
        try:
            upscale_process = subprocess.Popen([
                third_party_exe,
                "-i", temp_input_file,
                "-o", temp_output_file,
                "-n", model,
                "-s", str(4)
            ])
            upscale_process.wait()  # Wait for the process to complete

        except subprocess.CalledProcessError as e:
            gimp.message("Error during third-party processing: {}".format(str(e)))
            return

        # Step 4: Load the upscaled image and get the layer
        upscaled_image = pdb.gimp_file_load(temp_output_file, temp_output_file)
        upscaled_layer = pdb.gimp_image_get_active_layer(upscaled_image)  # Get the layer from the upscaled image

        # Step 5: Calculate the new dimensions based on the original image and the user-selected scale factor
        original_width = pdb.gimp_image_width(image)
        original_height = pdb.gimp_image_height(image)

        # Resize the upscaled image to match the user's desired scale factor
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        # Resize the upscaled image to the desired size
        pdb.gimp_image_scale(upscaled_image, new_width, new_height)

        # Resize the original image canvas to match the resized upscaled image
        pdb.gimp_image_resize(image, new_width, new_height, 0, 0)

        # Step 6: Copy the resized content into the original image's drawable, positioned at (0,0)
        pdb.gimp_edit_copy(upscaled_layer)  # Copy the upscaled layer content
        floating_sel = pdb.gimp_edit_paste(drawable, True)  # Paste into the original drawable
        pdb.gimp_layer_set_offsets(floating_sel, 0, 0)  # Ensure the pasted content is at the top-left (0, 0)
        pdb.gimp_floating_sel_anchor(floating_sel)  # Anchor the floating selection

        # Step 7: Clean up temporary files
        os.remove(temp_input_file)
        os.remove(temp_output_file)

        # Step 8: Flush the display to update the image in GIMP
        pdb.gimp_displays_flush()

    finally:
        # End the undo group (regardless of success or error)
        pdb.gimp_image_undo_group_end(image)  # Group end for undo/redo

# Register the function with GIMP
register(
    "python_fu_upscale_with_resrgan",
    "Upscale an image using a RESRGAN",
    "Upscale an image",
    "github/Nenotriple", "gimp_upscale", "2024",
    "<Image>/Filters/Enhance/AI Upscale (RESRGAN)...",
    "*",
    [
        (PF_SPINNER, "scale_factor", "Scale Factor", 1.0, (1.0, 4.0, 0.01)),  # User-selected floating-point scale factor
        (PF_OPTION, "model_index", "Model", 0, MODELS)  # Model selection
    ],
    [],
    upscale_with_third_party
)

main()
