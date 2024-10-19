<h1 align="center">
  <img src="https://github.com/user-attachments/assets/fd0b3a53-7240-4a01-8dff-5dcf4d0ca46b" alt="icon" width="50">
  gimp_upscale
</h1>


<p align="center">
  Upscale the current image using RESRGAN directly within GIMP
</p>


<p align="center">
  <img src="https://github.com/user-attachments/assets/a8b6a88e-a438-462e-8b97-e1e8091df748" alt="cover" width=512>
</p>


<p align="center">
  <em>(realesr-animevideov3, x1)</em>
</p>


> [!NOTE]
> Supports: `realesr-animevideov3-x4`, `RealESRGAN_General_x4_v3`, `realesrgan-x4plus`, `realesrgan-x4plus-anime`
> 
> Scale to any factor between, 1x to 4x
>
> Currently, only `Windows OS` is supported. If you're interested in testing a `Linux` or `Mac` plug-in, please create an issue.


<br>


# 💾 Install
![Static Badge](https://img.shields.io/badge/Windows-gray)
![Static Badge](https://img.shields.io/badge/GIMP-2.10%2B-green)


1) Download the latest release from the [releases page](https://github.com/Nenotriple/gimp_upscale/releases/tag/v1.0)
2) Extract the contents of the zip file to your GIMP plugins directory
   - Usually located at:
   - `C:\Users\%USERNAME%\AppData\Roaming\GIMP\2.10\plug-ins`
   - `C:\Program Files\GIMP 2\lib\gimp\2.0\plug-ins`

3) Restart GIMP

<br>


You can check the plugin directory by going to: `GIMP > Edit > Preferences > Folders > Plug-ins`


<br>


# 📝 Usage:

1) Open an image in GIMP

2) Go to `Filters > Enhance > AI Upscale (RESRGAN)...`

3) Choose the desired upscale factor and click `OK`

4) Wait for the image to be upscaled

<br>


# 👥 Thanks!

- [GIMP](https://www.gimp.org/) - *GPL-3.0*

- [xinntao - Real-ESRGAN_portable](https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn) - *BSD-3-Clause license*
