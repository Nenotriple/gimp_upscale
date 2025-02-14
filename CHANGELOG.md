### v1.04
[💾](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.04)


<details>
  <summary>Release Notes</summary>

### New:
- Add Tiled Upscale option.
  - Upscale the image in tiles to avoid memory issues (slower).


</details>


---


### v1.03
[💾](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.03)


<details>
  <summary>Release Notes</summary>

### New:
- Add Linux support.
- Add progress bar message during upscale process.

### Other Changes:
- Disable terminal popup on Windows.
- Increase output scale limits and granularity.


</details>


---


### v1.02
[💾](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.02)


<details>
  <summary>Release Notes</summary>


### Fixed:
- Fixed installation issue present is previous versions.


</details>


---


### v1.01
[💾](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.01)


<details>
  <summary>Release Notes</summary>


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


### v1.00
[💾](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.0)


<details>
  <summary>Release Notes</summary>


Initial release.


</details>

---
