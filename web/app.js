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
const exec = require('child_process').exec;

const settings = require('./settings');

const index_html = path.join(__dirname, 'index.html');
const register_html = path.join(__dirname, 'register.html');
const javascripts_dir = path.join(__dirname, 'res', 'javascripts');
const ajax = `<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>`;

// Resource directories
app.use('/css', express.static(path.join(__dirname, 'res', 'css')));
app.use('/media', express.static(path.join(__dirname, 'res', 'media')));
app.use(favicon(path.join(__dirname, 'res', 'media', 'favicon.ico')));

function fetch_file_contents(filename) {
    return new Promise((resolve, reject) => {
        fs.readFile(filename, 'utf-8', function (err, contents) {
            if (err) {
                console.log(err);
                reject('Could not read file: ' + filename);
            } else {
                resolve(contents);
            }
        });
    });
}

function fetch_static_javascript(filename) {
    return new Promise((resolve, reject) => {
        var git_ls = exec(`cd ${__dirname} && git ls-files`);

        // `git ls-files` always uses forward-slashes as path separator.
        var git_filepath = `res/javascripts/${filename}`;
        git_ls.stdout.on('data', (data) => {
            var lines = data.split(/\r?\n/);
            if (lines.indexOf(git_filepath) < 0) {
                console.log(`${filename} doesn't exist.`);
                reject('Attempting to load non-existent file.');
                return;
            } else {
                fetch_file_contents(path.join(javascripts_dir, filename))
                .then((contents) => {
                    resolve(contents);
                })
                .catch((err) => {
                    reject(err);
                });
            }
        });
    });
}

function render_static_javascript(filename, context) {
    return new Promise((resolve, reject) => {
        fetch_static_javascript(filename)
        .then((html) => {
            resolve(mustache.render(html, context));
        })
        .catch((err) => {
            reject(err);
        });
    });
}

function fetch_main_html() {
    // Load and return index.html contents
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
    // Load and return register.html contents
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
    // Renders mustache file with context
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
    // Renders the registration page
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
    // Check if a song id is in the url
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

app.use('/javascripts/:filename', function (req, res) {
    var context = {'api_url': settings['api_url']};

    render_static_javascript(req.params['filename'], context)
    .then((html) => {
        res.status(200).type('application/json').send(html);
    })
    .catch((err) => {
        console.log(err);
        res.status(500).send('Server error.');
    });
});

app.use('/register', function (req, res) {
    // Render the registration page
    var full_data = {};
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
    // Renders a page that makes an ajax request to refresh the database,
    //  then redirects to the main page.
    var api_url = settings['api_url'];
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://${api_url}/refresh'
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
    // Renders a page that makes an ajax request to restart the server,
    //  then redirects to the main page.
    var api_url = settings['api_url'];
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://${api_url}/restart'
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
    // Renders a page that makes an ajax request to remounts the media server,
    //  then redirects to the main page.
    var api_url = settings['api_url'];
    res.status(200).send(`
        <html><body>
        ${ajax}
        <script>
        $.ajax({
            type: 'GET',
            xhrFields: {
                withCredentials: true,
            },
            url: 'https://${api_url}/remount'
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

app.use('/robots.txt', function (req, res) {
    res.status(200).send(`
        User-agent: *\n
        Allow: /
    `)
})

app.use('/', function (req, res) {
    // Render the main page according to the parameters given.
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
            full_data['service_name'] = settings['service_name'];
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
                    let context = {};
                    context['service_name'] = settings['service_name'];
                    render_html(context)
                    .then(html => {
                        res.status(200).send(html);
                    })
                    .catch(err => {
                        console.log(err);
                        res.status(500).send('Server error.');
                    })
                }
            ).catch(
                (reason) => {
                    res.status(500).send('Error while loading page.');
                    console.log(reason);
                }
            );
        });
    } else {
        let context = {};
        context['service_name'] = settings['service_name'];
        render_html(context).then(
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
            return console.log("Error listening on port " + settings['webPort'] + ': ', err);
        }
        console.log((new Date()) + ': Web Server is listening on port ' + settings['webPort'] + '.');
    });
} else {
    app.listen(settings['webPort'], (err) => {
        if(err) {
            return console.log("Error listening on port " + settings['webPort'] + ': ', err);
        }
        console.log((new Date()) + ': Web Server is listening on port ' + settings['webPort'] + '.');
    });
}