# Lindelë
Lindele is a revamp of my first music streaming app to improve performance, maintainability, and to enable future projects. The name comes from the [Quenya word][1] for 'music'.

## Overview
The music player consists of two components: an API backend server, and a Node.js frontend server. The API backend does most of the heavy lifting, by managing the database interactions, and actually serving files to applications. The Node.js server mostly functions as a presentation app -- it generates visitable webpages, and those webpages actually make XHR requests to the API backend to dynamically update the page based on user interaction.

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

### Running the API
Depending on your setup, you may use a different method to run this application based on your needs. It is built to run using WSGI, and I personally use [waitress][2] to run the application on Windows, and [gunicorn][3] to run it on Linux. The commands to run it using each of these applications respectively are:
~~~~
waitress-serve --listen=*:80 main:app
~~~~
~~~~
gunicorn -b 0.0.0.0:80 main:app
~~~~

## Web Server Setup
### Installation
1. Make sure you have Node.js and NPM installed on your system.
2. Navigate to the `web` folder. 
3. Run `npm install`.

### Running the frontend
To run the Node.js server, you should only need to navigate to the appropriate folder and run `node app.js`

## Dependencies
1. [Python3][4]
2. [Node.js][5]

## Background
In 2018, I built a [music player][6] using Django so that I could more easily share my music collection with my family, as well as so I could access my music remotely. This also served as a key component of my resume for my first real job hunt, as a way to demonstrate my abilities as a developer. When I moved, however, I discovered that it was a lot more challenging to put back together and use based on that source code, and I realized that my ability to write code had improved significantly. 

With that in mind, I decided to rebuild it almost from the ground up, separating it into two components:
- An Python API that manages database interaction, and
- A Node.js web server that serves as a client for the user
This decision was influenced by another project I had started working on that used the same distinction between client-facing code and backend code. My original intention with this was to make it easier for users to write their own clients if they so chose, as well as to make a unified back-end so I could eventually write a mobile application myself. For the API backend, I ended up falling in love with [pycnic][7], and wanted to see how quickly I could rebuild the Django music player with this new design principle.

[1]:https://www.elfdict.com/w/lindele
[2]:https://github.com/Pylons/waitress
[3]:https://gunicorn.org/
[4]:https://www.python.org
[5]:https://nodejs.org
[6]:https://github.com/tfdahlin/music_stream
[7]:http://pycnic.nullism.com