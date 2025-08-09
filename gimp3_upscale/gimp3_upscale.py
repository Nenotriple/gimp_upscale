#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Upscale (GIMP 3)
- Auto-discovers valid Real-ESRGAN models (paired .bin/.param) in resrgan/models.
- Presents models as radio buttons in the ProcedureDialog (single selection).
- Runs realesrgan-ncnn-vulkan with the chosen model and inserts the result.
- Can apply to the entire image, only to the current selection, or to the selected layer only.
"""


#region Imports


import sys
import os
import tempfile
import subprocess
from pathlib import Path
import platform  # added

import gi  # type: ignore
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gegl', '0.4')
gi.require_version('Gtk', '3.0')

from gi.repository import Gimp, GimpUi, Gegl, GObject, GLib, Gio, Gtk  # type: ignore


#endregion
#region Utils


def _txt(message: str) -> str:
    """Translate the given message using GLib's dgettext for localization."""
    return GLib.dgettext(None, message)


def _return_error(procedure, status: Gimp.PDBStatusType, message: str):
    """Create a GLib.Error with message and return standardized return values."""
    err = GLib.Error()
    err.message = message
    return procedure.new_return_values(status, err)


def _del_file(path: str):
    """Silently remove a file if it exists."""
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def _progress_start(message: str):
    """Initialize and show progress in the status bar."""
    try:
        Gimp.progress_init(message)
    except Exception:
        pass
    Gimp.progress_set_text(message)
    try:
        Gimp.progress_update(0.0)
    except Exception:
        pass


def _progress(message: str, fraction: float | None = None):
    """Update status text and optionally progress fraction [0..1]."""
    Gimp.progress_set_text(message)
    if fraction is not None:
        f = max(0.0, min(1.0, float(fraction)))
        try:
            Gimp.progress_update(f)
        except Exception:
            pass


#endregion
#region Paths & consts


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RESRGAN_DIR = os.path.join(SCRIPT_DIR, "resrgan")
MODELS_DIR = os.path.join(RESRGAN_DIR, "models")
DEFAULT_OUTPUT_FACTOR = 1.0


# Platform detection
PLATFORM = platform.system()
if PLATFORM == "Windows":
    RESRGAN_PATH = os.path.join(RESRGAN_DIR, "realesrgan-ncnn-vulkan.exe")
    SHELL = True
else: # linux
    RESRGAN_PATH = os.path.join(RESRGAN_DIR, "realesrgan-ncnn-vulkan")
    SHELL = False
    # Make sure the executable has the correct permissions
    subprocess.call(['chmod', 'u+x', RESRGAN_PATH])


#endregion
#region Models


def _resolve_resrgan_executable() -> str:
    """Resolve the resrgan binary based on platform"""
    if not os.path.isfile(RESRGAN_PATH):
        raise FileNotFoundError(f"Real-ESRGAN executable not found at: {RESRGAN_PATH}")
    return RESRGAN_PATH


def _find_valid_models(models_dir: str) -> list[str]:
    """
    Return sorted list of model stems that have matching .bin and .param files.
    A model is valid only if both files with the same stem exist.
    """
    p = Path(models_dir)
    if not p.is_dir():
        return []
    stems_bin = {f.stem for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".bin"}
    stems_param = {f.stem for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".param"}
    return sorted(stems_bin.intersection(stems_param))


#endregion
#region IO helpers


def _export_drawable_to_temp(drawable: Gimp.Drawable) -> str:
    """Export drawable to a temporary PNG file using GIMP 3 PDB export."""
    temp_file = tempfile.mktemp(suffix=".png")
    image = drawable.get_image()
    file = Gio.File.new_for_path(temp_file)
    pdb = Gimp.get_pdb()
    procedure = pdb.lookup_procedure('file-png-export')
    if procedure is None:
        raise RuntimeError("Missing 'file-png-export' procedure.")
    config = procedure.create_config()
    config.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
    config.set_property('image', image)
    config.set_property('file', file)
    procedure.run(config)
    return temp_file


def _load_png_as_image(path: str) -> Gimp.Image:
    """Load a PNG file as a GIMP image using GIMP 3 PDB load."""
    pdb = Gimp.get_pdb()
    load_proc = pdb.lookup_procedure('file-png-load')
    if load_proc is None:
        raise RuntimeError("Missing 'file-png-load' procedure.")
    cfg = load_proc.create_config()
    cfg.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
    cfg.set_property('file', Gio.File.new_for_path(path))
    result = load_proc.run(cfg)
    # In GIMP 3, result[1] is image, result[2] is drawable when available.
    return result.index(1)


def _run_resrgan(temp_input: str, temp_output: str, model: str):
    """
    Run Real-ESRGAN upscaling. We set cwd to RESRGAN_DIR so '-n <model>'
    can resolve model files in ./models automatically.
    """
    exe_path = _resolve_resrgan_executable()
    try:
        proc = subprocess.Popen(
            [exe_path, "-i", temp_input, "-o", temp_output, "-n", model],
            cwd=RESRGAN_DIR,
            shell=SHELL,  # match gimp2_upscale.py behavior
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                "Real-ESRGAN failed.\n"
                f"Command: {exe_path} -i \"{temp_input}\" -o \"{temp_output}\" -n \"{model}\"\n"
                f"stdout:\n{stdout.decode(errors='ignore')}\n\n"
                f"stderr:\n{stderr.decode(errors='ignore')}"
            )
    except Exception as e:
        raise RuntimeError(f"Error running Real-ESRGAN: {e}") from e


def _export_layer_only_to_temp(image: Gimp.Image, layer: Gimp.Layer) -> str:
    """
    Export only the given layer composited on transparency (no merging with other layers).
    Implementation: temporarily toggle visibility to export the composite with only this layer visible.
    """
    temp_file = tempfile.mktemp(suffix=".png")
    pdb = Gimp.get_pdb()
    export_proc = pdb.lookup_procedure('file-png-export')
    if export_proc is None:
        raise RuntimeError("Missing 'file-png-export' procedure.")
    # Snapshot current visibility of all layers
    layers = list(image.get_layers())
    vis_map = [(l, l.get_visible()) for l in layers]
    try:
        # Hide all, show only requested layer
        for l in layers:
            l.set_visible(False)
        layer.set_visible(True)
        # Export the image composite (now effectively just this layer)
        file = Gio.File.new_for_path(temp_file)
        cfg = export_proc.create_config()
        cfg.set_property('run-mode', Gimp.RunMode.NONINTERACTIVE)
        cfg.set_property('image', image)
        cfg.set_property('file', file)
        export_proc.run(cfg)
    finally:
        # Restore visibilities
        for l, v in vis_map:
            try:
                l.set_visible(v)
            except Exception:
                pass
    return temp_file


#endregion
#region Compose


def _image_layer_type(image: Gimp.Image) -> Gimp.ImageType:
    return Gimp.ImageType.RGBA_IMAGE if image.get_base_type() == Gimp.ImageBaseType.RGB else Gimp.ImageType.GRAYA_IMAGE


def _scaled_canvas_size(image: Gimp.Image, factor: float) -> tuple[int, int]:
    orig_w, orig_h = image.get_width(), image.get_height()
    final_w = max(1, int(round(orig_w * factor)))
    final_h = max(1, int(round(orig_h * factor)))
    return final_w, final_h


def _new_layer(image: Gimp.Image, name: str, width: int, height: int) -> Gimp.Layer:
    layer_type = _image_layer_type(image)
    new_layer = Gimp.Layer.new(image, name, width, height, layer_type, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(new_layer, None, -1)
    return new_layer


def _scale_and_copy(src: Gimp.Layer, dst: Gimp.Layer, width: int, height: int) -> None:
    src.scale(width, height, False)
    src_buf = src.get_buffer()
    dst_buf = dst.get_buffer()
    rect = Gegl.Rectangle.new(0, 0, width, height)
    src_buf.copy(rect, Gegl.AbyssPolicy.NONE, dst_buf, rect)
    dst.update(0, 0, width, height)


def _handle_upscaled_layer(image: Gimp.Image, upscaled_layer: Gimp.Layer, output_factor: float) -> Gimp.Layer:
    """
    Insert the upscaled layer into image, resize canvas to factor * original, and fit content.
    """
    final_w, final_h = _scaled_canvas_size(image, output_factor)
    image.resize(final_w, final_h, 0, 0)
    new_layer = _new_layer(image, "AI Upscaled Layer", final_w, final_h)
    _scale_and_copy(upscaled_layer, new_layer, final_w, final_h)
    return new_layer


def _handle_upscaled_selection(image: Gimp.Image, upscaled_layer: Gimp.Layer) -> Gimp.Layer:
    """
    Insert upscaled content on same canvas and reveal only inside current selection.
    """
    width, height = image.get_width(), image.get_height()
    new_layer = _new_layer(image, "AI Upscaled (Selection)", width, height)
    _scale_and_copy(upscaled_layer, new_layer, width, height)
    mask = new_layer.create_mask(Gimp.AddMaskType.SELECTION)
    new_layer.add_mask(mask)
    return new_layer


def _handle_upscaled_layer_only(image: Gimp.Image, upscaled_layer: Gimp.Layer, output_factor: float) -> Gimp.Layer:
    """
    Insert upscaled layer and resize canvas like 'Entire image' without selection masking.
    """
    final_w, final_h = _scaled_canvas_size(image, output_factor)
    image.resize(final_w, final_h, 0, 0)
    new_layer = _new_layer(image, "AI Upscaled (Layer only)", final_w, final_h)
    _scale_and_copy(upscaled_layer, new_layer, final_w, final_h)
    return new_layer


#endregion
#region Procedure run


def ai_upscale(procedure, run_mode, image, drawables, config, data):
    """
    Main entry:
      - Discover models
      - Present radio buttons (interactive)
      - Run Real-ESRGAN with selected model
      - Insert result (entire image, selection only, or layer only)
    """
    # Discover model options up front
    model_options = _find_valid_models(MODELS_DIR)
    if not model_options:
        msg = (
            "No valid models found.\n\n"
            "A valid model requires a matching .bin/.param pair with the same filename stem.\n"
            f"Expected in:\n{MODELS_DIR}"
        )
        Gimp.message(msg)
        return _return_error(procedure, Gimp.PDBStatusType.EXECUTION_ERROR, msg)

    # Use local defaults instead of config-backed properties
    current_model = model_options[0]
    scope_mode = "entire"  # 'entire' | 'selection' | 'layer'
    # Interactive UI
    if run_mode == Gimp.RunMode.INTERACTIVE:
        #region GUI
        # --- Dialog ---
        GimpUi.init('python-fu-ai-upscale')
        _progress("AI Upscale: choose model and scope…")
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)  # Only 'output_factor' remains as a real argument
        # --- Model radios ---
        frame = Gtk.Frame.new(_txt("Model"))
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        frame.add(vbox)
        radio_group = None
        for stem in model_options:
            btn = Gtk.RadioButton.new_with_label_from_widget(radio_group, stem)
            if radio_group is None:
                radio_group = btn
            if stem == current_model:
                btn.set_active(True)
            def _on_toggle(button, s=stem):
                nonlocal current_model
                if button.get_active():
                    current_model = s
            btn.connect('toggled', _on_toggle)
            vbox.pack_start(btn, False, False, 0)
        dialog.get_content_area().pack_start(frame, False, False, 6)
        # --- Scope radios ---
        scope_frame = Gtk.Frame.new(_txt("Scope"))
        scope_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scope_frame.add(scope_box)
        rb_entire = Gtk.RadioButton.new_with_label_from_widget(None, _txt("Entire image"))
        rb_selection = Gtk.RadioButton.new_with_label_from_widget(rb_entire, _txt("Selection only"))
        rb_layer = Gtk.RadioButton.new_with_label_from_widget(rb_entire, _txt("Layer only"))
        rb_entire.set_active(scope_mode == "entire")
        rb_selection.set_active(scope_mode == "selection")
        rb_layer.set_active(scope_mode == "layer")

        def _on_scope_toggle(btn, val):
            nonlocal scope_mode
            if btn.get_active():
                scope_mode = val

        rb_entire.connect('toggled', _on_scope_toggle, "entire")
        rb_selection.connect('toggled', _on_scope_toggle, "selection")
        rb_layer.connect('toggled', _on_scope_toggle, "layer")
        scope_box.pack_start(rb_entire, False, False, 0)
        scope_box.pack_start(rb_selection, False, False, 0)
        scope_box.pack_start(rb_layer, False, False, 0)
        dialog.get_content_area().pack_start(scope_frame, False, False, 6)
        dialog.show_all()
        # --- Run & close ---
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()
        #endregion

    # Non-interactive or interactive continues:
    output_factor = float(config.get_property('output_factor'))
    if not drawables:
        return _return_error(procedure, Gimp.PDBStatusType.EXECUTION_ERROR, "No drawable selected.")

    # Do the work
    Gimp.context_push()
    image.undo_group_start()
    # Initialize status bar progress
    _progress_start("AI Upscale: starting…")
    try:
        total = len(drawables)
        for idx, drawable in enumerate(drawables):
            base = idx / total
            span = 1.0 / total
            _progress(f"Exporting layer {idx+1}/{total}…", base + 0.02 * span)
            if scope_mode == "layer":
                temp_input = _export_layer_only_to_temp(image, drawable)
            else:
                temp_input = _export_drawable_to_temp(drawable)  # exports the image composite

            temp_output = tempfile.mktemp(suffix=".png")
            upscaled_image = None
            try:
                _progress(f"Upscaling with {current_model}…", base + 0.15 * span)
                _run_resrgan(temp_input, temp_output, current_model)
                _progress("Loading upscaled image…", base + 0.60 * span)
                upscaled_image = _load_png_as_image(temp_output)
                upscaled_layers = upscaled_image.get_layers()
                if not upscaled_layers:
                    raise RuntimeError("Upscaled image has no layers.")
                upscaled_layer = upscaled_layers[0]
                if scope_mode == "selection":
                    _progress("Compositing into selection…", base + 0.75 * span)
                    _handle_upscaled_selection(image, upscaled_layer)
                elif scope_mode == "layer":
                    _progress("Compositing layer…", base + 0.80 * span)
                    _handle_upscaled_layer_only(image, upscaled_layer, output_factor)
                else:
                    _progress("Compositing result…", base + 0.80 * span)
                    _handle_upscaled_layer(image, upscaled_layer, output_factor)
                _progress(f"Finalizing {idx+1}/{total}…", base + 0.95 * span)
            finally:
                _del_file(temp_input)
                _del_file(temp_output)
                try:
                    if upscaled_image is not None:
                        upscaled_image.delete()
                except Exception:
                    pass
            # Mark per-drawable completion
            _progress(f"Completed {idx+1}/{total}", (idx + 1) / total)
        Gimp.displays_flush()
        _progress("AI Upscaling complete!", 1.0)
    except Exception as e:
        return _return_error(procedure, Gimp.PDBStatusType.EXECUTION_ERROR, f"Upscaling failed: {e}")
    finally:
        image.undo_group_end()
        Gimp.context_pop()
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


#endregion
#region AIUpscale


class AIUpscale(Gimp.PlugIn):
    # GimpPlugIn virtual methods
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None


    def do_query_procedures(self):
        return ['python-fu-ai-upscale']


    def do_create_procedure(self, name):
        proc = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, ai_upscale, None)
        proc.set_image_types("RGB*, GRAY*")
        proc.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.DRAWABLES)
        proc.set_documentation(
            _txt("AI-powered image upscaling"),
            _txt("Upscale images using Real-ESRGAN AI models discovered in resrgan/models"),
            name
        )
        proc.set_menu_label(_txt("AI _Upscale…"))
        proc.set_attribution("github.com/Nenotriple", "github.com/Nenotriple", "2025")
        proc.add_menu_path("<Image>/Filters/Enhance")
        # radio buttons defined in GUI region handle model and scope.
        proc.add_double_argument(
            "output_factor",
            _txt("Output _Factor"),
            _txt("Final output size relative to original size (entire image mode)"),
            0.05, 8.0, DEFAULT_OUTPUT_FACTOR,
            GObject.ParamFlags.READWRITE
        )
        return proc


#endregion
Gimp.main(AIUpscale.__gtype__, sys.argv)


#endregion
