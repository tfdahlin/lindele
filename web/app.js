"use strict";

process.title = 'Music stream';

const path = require('path');
const http = require('http');
const https = require('https');
const express = require('express');
const app = express();
const favicon = require('serve-favicon');
const fs = require('fs');
const mustache = require('mustache');
const axios = require('axios');

const settings = require('./settings');

const index_html = path.join(__dirname, 'index.html');
const register_html = path.join(__dirname, 'register.html');
const ajax = `<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>`;

app.use('/css', express.static(path.join(__dirname, 'res', 'css')));

app.use('/javascripts', express.static(path.join(__dirname, 'res', 'javascripts')));

app.use('/media', express.static(path.join(__dirname, 'res', 'media')));

app.use(favicon(path.join(__dirname, 'res', 'media', 'favicon.ico')));

function fetch_main_html() {
    return new Promise((resolve, reject) => {
        fs.readFile(index_html, 'utf-8', function(err, contents) {
            if (err) {
                reject('Could not read file: ' + index_html);
            } else {
                resolve(contents);
            }
        });
    });
}

function fetch_register_html() {
    return new Promise((resolve, reject) => {
        fs.readFile(register_html, 'utf-8', function(err, contents) {
            if (err) {
                reject('Could not read file: ' + register_html);
            } else {
                resolve(contents);
            }
        });
    });
}

function render_html(context) {
    return new Promise((resolve, reject) => {
        fetch_main_html()
        .then(html => {
            try {
                resolve(mustache.render(html, context));
            } catch {
                reject('Failed to render template.');
            }
        })
        .catch(err => {
            reject(err);
        });
    });
}

function render_register_html(context) {
    return new Promise((resolve, reject) => {
        fetch_register_html()
        .then(html => {
            try {
                resolve(mustache.render(html, context));
            } catch {
                reject('Failed to render template.');
            }
        })
        .catch(err => {
            reject(err);
        });
    });
}

function has_song_id(req) {
    if (!Object.keys(req.query).length) {
        return false;
    }
    if (!req.query['songid']) {
        return false;
    }
    if (req.query['songid'] === 'undefined') {
        return false;
    }
    if (req.query['songid'] === undefined) {
        return false;
    }
    return true;
}

app.use('/register', function (req, res) {
    var full_data = {}
    render_register_html(full_data)
        .then(html => {
            res.status(200).send(html);
        })
        .catch(err => {
            console.log(err);
            res.status(500).send('Server error.');
        });
});

app.use('/refresh', function (req, res) {
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://api.music.acommplice.com/refresh'
        })
        .done((data) => {
            window.location.href = '/';
        })
        .fail((err) => {
            console.log(err);
            window.location.href = '/';
        })
        </script>
        </html></body>
    `)
});

app.use('/restart', function (req, res) {
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://api.music.acommplice.com/restart'
        })
        .done((data) => {
            window.location.href = '/';
        })
        .fail((err) => {
            console.log(err);
            window.location.href = '/';
        })
        </script>
        </html></body>

    `)
});

app.use('/remount', function (req, res) {
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://api.music.acommplice.com/remount'
        })
        .done((data) => {
            /*window.location.href = '/';*/
        })
        .fail((err) => {
            console.log(err);
            /*window.location.href = '/';*/
        })
        </script>
        </html></body>

    `)
});

app.use('/', function (req, res) {
    if (has_song_id(req)) {
        let songid = req.query['songid'];
        console.log(songid)
        console.log(typeof(songid));

        let song_url = settings['api_url'] + '/songs/' + songid;

        axios.get(song_url)
        .then(response => {
            console.log(response.data['data']);
            let full_data = response.data['data'];
            full_data['songid'] = songid;
            full_data['artwork_url'] = settings['api_url'] + '/songs/' + songid + '/artwork';
            full_data['api_url'] = settings['api_url'];
            full_data['song_url'] = song_url;
            render_html(full_data)
            .then(html => {
                res.status(200).send(html);
            })
            .catch(err => {
                console.log(err);
                res.status(500).send('Server error.');
            });
        })
        .catch(error => {
            console.log(error);
            
            // Load main page
            fetch_main_html().then(
                (contents) => {
                    res.status(200).send(contents);
                }
            ).catch(
                (reason) => {
                    res.status(500).send('Error while loading page.');
                    console.log(reason);
                }
            );
        });
    } else {
        render_html({}).then(
            (contents) => {
                res.status(200).send(contents);
            }
        ).catch(
            (reason) => {
                res.status(500).send('Error while loading page.');
                console.log(reason);
            }
        );
    }
});

if(settings['https']) {
    https.createServer({
        key: fs.readFileSync(settings['ssl_key_path']),
        cert: fs.readFileSync(settings['ssl_cert_path']),
        ca: fs.readFileSync(settings['ssl_ca_path'])
    }, app)
    .listen(settings['webPort'], (err) => {
        if(err) {
            return console.log("Error listening on port " + webPort + ': ', err);
        }
        console.log((new Date()) + ': Web Server is listening on port ' + webPort + '.');
    });
} else {
    app.listen(settings['webPort'], (err) => {
        if(err) {
            return console.log("Error listening on port " + webPort + ': ', err);
        }
        console.log((new Date()) + ': Web Server is listening on port ' + webPort + '.');
    });
}