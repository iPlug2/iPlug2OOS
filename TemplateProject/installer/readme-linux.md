# TemplateProject

This archive contains the TemplateProject standalone application, and VST3 and CLAP plug-ins for Linux.

## Installation

Copy the plug-ins to your user plug-in folders. Each `.resources` folder must stay next to the file it belongs to.

- **VST3:** copy `TemplateProject.vst3` to `~/.vst3/`
- **CLAP:** copy `TemplateProject.clap` and `TemplateProject.clap.resources` to `~/.clap/`
- **Standalone:** keep `TemplateProject` and `TemplateProject.resources` together in a folder of your choice, and run `./TemplateProject`

## Requirements

TemplateProject needs X11, OpenGL 3, GTK 3 and fontconfig. The standalone application can use ALSA, JACK or PulseAudio for audio, and needs the ALSA, JACK and PulseAudio client libraries to be installed.

If you experience any problems with TemplateProject, please contact us at:

support@acmeinc.com
