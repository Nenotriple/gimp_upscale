<h1 align="center">
  <img src="https://github.com/user-attachments/assets/fd0b3a53-7240-4a01-8dff-5dcf4d0ca46b" alt="icon" width="50">
  gimp_upscale
</h1>


<p align="center">
  Upscale directly within GIMP using realesrgan-ncnn-vulkan
</p>


![Compare_split_test](https://github.com/user-attachments/assets/63584ff7-6bc5-4307-a0f6-1a9aa6864303)


![GitHub repo size](https://img.shields.io/github/repo-size/Nenotriple/gimp_upscale)
![GitHub all release downloads](https://img.shields.io/github/downloads/Nenotriple/gimp_upscale/total)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/Nenotriple/gimp_upscale)


# Features


- Choose between 6 built-in models:
  - `realesr-animevideov3-x4`, `RealESRGAN_General_x4_v3`,
  - `realesrgan-x4plus`, `realesrgan-x4plus-anime`,
  - `UltraSharp-4x`, `AnimeSharp-4x`
- Upscale the entire layer, or just the selection.
- Scale the output to any factor from 0.1x to 8x
- Create a copy of the original selection when upscaling just the selection.
- Cleanly upscale transparent alpha channels.
- Use any other custom 4x ESRGAN model.


<details>
<summary>Adding your own custom ESRGAN models to the plug-in...</summary>
  
- Add your own models (NCNN) to the `resrgan/models` folder.
  - Additional models can be found at https://openmodeldb.info/
  - At this time, only `4x`/`x4` models are supported.
  - Please ensure the custom model includes a `model.param` and a `model.bin` file.
    - `.pth` model format is *not* supported.
  - Models can be converted to NCNN format with tools like:
    - [Chainner,](https://github.com/chaiNNer-org/chaiNNer) or [custom scripts](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/issues/59#issuecomment-2078688728)
</details>


> [!NOTE]
> - Please see this [issue page](https://github.com/Nenotriple/gimp_upscale/issues/6) if you're interested in testing a MacOS version, let me know how it works!

<br>


# 💾 Install
![Static Badge](https://img.shields.io/badge/GIMP-2.10%2B-green)


![Static Badge](https://img.shields.io/badge/Windows-blue)
![Static Badge](https://img.shields.io/badge/Linux-orange)


![Static Badge](https://img.shields.io/badge/Intel-blue) ![Static Badge](https://img.shields.io/badge/AMD-red) ![Static Badge](https://img.shields.io/badge/Nvidia-green)


### Method 1
1) Download the [latest release](https://github.com/Nenotriple/gimp_upscale/releases)
2) Extract the zip file to your GIMP plugins directory
3) Restart GIMP


### Method 2
1) Clone this repo
2) Open GIMP and go to: `GIMP > Edit > Preferences > Folders > Plug-ins`
3) Add the repo path to your plug-in folders
4) Restart GIMP

### Extra info
<details>
<summary>Find your GIMP plug-in directory...</summary>

- You can always find you plug-in folder from:
  - `GIMP > Edit > Preferences > Folders > Plug-ins`
- Default directory for Windows:
  - `C:\Users\%USERNAME%\AppData\Roaming\GIMP\2.10\plug-ins`
  - `C:\Program Files\GIMP 2\lib\gimp\2.0\plug-ins`
- Default directory for Linux:
  - `~/.config/GIMP/2.10/plug-ins`
  - `~/.gimp-2.10/plug-ins`

</details>


<details>
<summary>Example directory structure...</summary>
  
GIMP plug-ins must be in a folder structure like this:

```plaintext
plug-ins
|
└── gimp_upscale
    |
    └── gimp_upscale.py
```

</details>


<details>
<summary>Additional information for Linux...</summary>
  
Setting up Python in GIMP on Linux may require additional steps.

If you're having trouble, you can check the resources below:
- The official [GIMP download page](https://www.gimp.org/downloads/).
  - The flatpak version of GIMP should come with Python support.
- Prebuilt GIMP Appimages; eg. [From here,](https://github.com/aferrero2707/gimp-appimage/releases/tag/continuous) or [from here,](https://github.com/TasMania17/Gimp-Appimages-Made-From-Debs/releases/tag/Gimp-v3.0.0rc1) etc.
- Install `gimp-python` from your package manager.

</details>


<br>


# 📝 Usage


1) Open an image in GIMP
2) Go to `Filters > Enhance > AI Upscale (NCNN)...`
3) Choose the desired settings and click `OK`
4) Wait for the image to be upscaled


<br>


# 🌟 Projects Using `gimp_upscale`

Here are some awesome projects that have used `gimp_upscale`:

| Creator | Description | Project Link |
| - | - | - |
| [@typokiow](https://next.nexusmods.com/profile/typokiow?gameId=7587) | **HQ Oblivion in-game map** — Replace the world map making it sharper and more legible whithout altering the original aesthetic.  | https://www.nexusmods.com/oblivionremastered/mods/1598?tab=description |

> 🎨 **Have you used `gimp_upscale` in a project?**
> [Open an issue](https://github.com/Nenotriple/gimp_upscale/issues) to be featured here!


# 👥 Thanks!

- [GIMP](https://www.gimp.org/) - *GPL-3.0*

- [xinntao - Real-ESRGAN_portable](https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn) - *BSD-3-Clause license*

