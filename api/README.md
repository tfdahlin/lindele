# Lindele API

The Lindele API is a RESTful API server built using the Pycnic framework.
It is designed to work like a personal media server, serving a personal
collection of music. 

Lindele has a few expectations in order to function correctly. For one, it
loads album artwork by searching the folder that the audio track is stored in,
and it will use the first `.jpeg`, `.jpg`, or `.png` file that it finds in the
folder. If it is unable to find this album artwork, it will use a default
album artwork missing image. 

Notes:
- Lindele currently only supports `.mp3` audio files.
- Lindele currently only supports `.jpeg`, `.jpg`, and `.png` artwork files.

[API endpoint documentation](docs/endpoints.md)