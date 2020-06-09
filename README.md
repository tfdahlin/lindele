# Lindelë
Lindelë is a revamp of my first music streaming app to improve performance,
maintainability, and to enable future projects. The name comes from the
[Quenya word][1] for 'music'.

## Overview
The music player consists of two components: an API backend server, and a
Node.js frontend server. The API backend does most of the heavy lifting, by
managing the database interactions, and actually serving files to applications.
The Node.js server mostly functions as a presentation app -- it generates
visitable webpages, and those webpages actually make XHR requests to the API
backend to dynamically update the page based on user interaction.

## API
Comprehensive details about the api component, including setup instructions, 
can be found in its [README](api/README.md).

## Web Server
Comprehensive details about the web server component, including setup 
instructions, can be found in its [README](web/README.md).

## Background
In 2018, I built a [music player][2] using Django so that I could more easily
share my music collection with my family, as well as so I could access my music
remotely. This also served as a key component of my resume for my first real
job hunt, as a way to demonstrate my abilities as a developer. When I moved,
however, I discovered that it was a lot more challenging to put back together
and use based on that source code, and I realized that my ability to write code
had improved significantly. 

With that in mind, I decided to rebuild it almost from the ground up,
separating it into two components:
- An Python API that manages database interaction, and
- A Node.js web server that serves as a client for the user
This decision was influenced by another project I had started working on that
used the same distinction between client-facing code and backend code. My
original intention with this was to make it easier for users to write their own
clients if they so chose, as well as to make a unified back-end so I could
eventually write a mobile application myself. For the API backend, I ended up
falling in love with [pycnic][3], and wanted to see how quickly I could rebuild
the Django music player with this new design principle.

[1]:https://www.elfdict.com/w/lindele
[2]:https://github.com/tfdahlin/music_stream
[3]:http://pycnic.nullism.com