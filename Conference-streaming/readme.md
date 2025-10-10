# Conference streaming

We stream using [OBS](https://obsproject.com/).

# Video

## Video from presentation screen

This can come a stream at the venue, or via a capture card. We have an Elgato HD60X.

We also have a (powered) HDMI splitter.

## Video from cellphones

We use https://vdo.ninja/ for a no-installation way to get a stream from a cellphone camera into OBS. Each phone will have an ID that persists across power cycles.

To add a vdo.ninja stream into OBS, add a "Browser" video source, and put in the generate URL.

## Outgoing video stream

Start the virtual camera in OBS - this will broadcast the current scene, and can be selected as the camera in Zoom, Hyhyve, etc. You can also stream directly to services like Youtube.

Note: Youtube has a 24-hour delay to enable live streaming on any account! Make sure to enable this in time if you want to use it as a backup.

# Audio

The OBS virtual camera is video only. Audio is a separate stream.

Make sure to look in the advanced audio OBS settings - by default, any incoming audio stream is *silenced*. You need to change this to "Monitor and Output" for the incoming audio streams you want.

Use https://github.com/ExistentialAudio/BlackHole/ on MacOS to create a virtual audio device. In the OBS audio settings this can be the monitor device. It can also be the microphone in Zoom, Hyhyve, etc.
