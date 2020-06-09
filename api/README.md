# Lindelë API

The Lindelë API is a RESTful API server built using the Pycnic framework.
It is designed to work like a personal media server, serving a personal
collection of music. 

Lindelë has a few expectations in order to function correctly. For one, it
loads album artwork by searching the folder that the audio track is stored in,
and it will use the first `.jpeg`, `.jpg`, or `.png` file that it finds in the
folder. If it is unable to find this album artwork, it will use a default
album artwork missing image. 

Notes:
- Lindelë currently only supports `.mp3` audio files.
- Lindelë currently only supports `.jpeg`, `.jpg`, and `.png` artwork files.

## Setup
### Installation
1. Make sure that you have [python3][1] and python3-pip installed on your system.
2. Clone this repository, then navigate to the `api` folder.
3. [Optional] Set up and activate a virtual environment for the application.
    - This can be accomplished by running `python3 -m venv env`, then
    running `. env/bin/activate`.
4. Run `pip3 install -r requirements.txt` to install required libraries.
5. Run `python wizard.py` to guide you through creating a `local_settings.py` file.
    - This includes detailed instructions for different environments, please
    read the instructions carefully.
6. If necessary, write a mounting script. In my case, it looked something like this:
~~~~
#!/bin/bash

sudo mount -t cifs -v -o vers=3.0,username=media_server_username,password=media_server_password,ip=192.168.1.100 //MEDIA_SERVER_NAME/Music /mnt/Music
~~~~

### Running the API
Depending on your setup, you may use a different method to run this application based on your needs. It is built to run using WSGI, and I personally use [waitress][2] to run the application on Windows, and [gunicorn][3] to run it on Linux. The commands to run it on port 80 using each of these applications respectively are:
~~~~
waitress-serve --listen=*:8000 main:app
~~~~
~~~~
gunicorn -b 0.0.0.0:8000 main:app
~~~~

### Documentation
Documentation about the available API endpoints can be found 
[here](docs/endpoints.md)

[1]:https://www.python.org
[2]:https://github.com/Pylons/waitress
[3]:https://gunicorn.org/