### v1.01 - 2024-10-20
[💾v1.01](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.01)


<details>
  <summary>Release Notes for v1.01</summary>


### New:
- **Upscale Selected Content**:
  - Upscale only the selected content.
  - The selection is upscaled and pasted back into the original position on a new layer.
  - The scale factor is always "1x" when upscaling the selection.
- **Load Additional Models**:
  - Load additional models in NCNN format.
  - The script searches for models in the `resrgan\models` folder.
  - Each model must include a `model.param` and a `model.bin` file.
- **New Models**:
  - Two additional models: `4x-UltraSharp` and `4x-AnimeSharp`.


### Fixed:
- Fixed the issue where the script would fail when using a scale factor other than 1x.


### Other changes:
- Refactored and organized the code.


</details>

---


### v1.00 - 2024-10-18
[💾v1.00](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.00)


<details>
  <summary>Release Notes for v1.00</summary>


Initial release.


</details>

---