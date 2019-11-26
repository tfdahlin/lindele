# music_stream_revamp
Revamp of my first music stream app to improve performance, maintainability, and to enable future projects.

## Overview
In 2018, I built a [music player][1] using Django so that I could more easily share my music collection with my family, as well as so I could access my music remotely. This also served as a key component of my resume for my first real job hunt, as a way to demonstrate my abilities as a developer. When I moved, however, I discovered that it was a lot more challenging to put back together and use based on that source code, and I realized that my ability to write code had improved significantly. 

With that in mind, I decided to rebuild it almost from the ground up, separating it into two components:
- An Python API that manages database interaction, and
- A Node.js web server that serves as a client for the user
This decision was influenced by another project I had started working on that used the same distinction between client-facing code and backend code. My original intention with this was to make it easier for users to write their own clients if they so chose, as well as to make a unified back-end so I could eventually write a mobile application. I ended up falling in love with [pycnic][2], and wanted to play around with it some more for fun, and wanted to see how quickly I could rebuild the Django functionality in a new project.

The web server static javascript files are written with 

## API Setup
### Installation
1. Make sure that you have python3 and python3-pip installed on your system.
2. Clone this repository, then navigate to the `api` folder.
3. [Optional] Set up and activate a virtual environment for the application.
4. Run `pip3 install -r requirements.txt`
5. Create a file called `local_settings.py` in the `api` folder.
6. Go through `settings.py` and adjust `local_settings.py` according to the instructions and your specific requirements.
7. If necessary, write a mounting script. In my case, it looked something like this:
~~~~
#!/bin/bash

sudo mount -t cifs -v -o vers=3.0,username=media_server_username,password=media_server_password,ip=192.168.1.100 //MEDIA_SERVER_NAME/Music /mnt/Music
~~~~

## Web Server Setup
### Installation
1. Make sure you have Node.js and NPM installed on your system.
2. Navigate to the `web` folder. 
3. Run `npm install`.

## Dependencies
1. Python3 (https://www.python.org)

2. Node.js (https://nodejs.org)

[1]:https://github.com/tfdahlin/music_stream
[2]:http://pycnic.nullism.com