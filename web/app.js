"use strict";

process.title = 'Music stream';

const path = require('path');
const http = require('http');
const express = require('express');
const app = express();
const favicon = require('serve-favicon');
const fs = require('fs');

const webPort = 8080;

const index_html = path.join(__dirname, 'index.html');

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

app.use('/', function (req, res) {
    console.log('Reached page: /');
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

app.listen(webPort, (err) => {
    if(err) {
        return console.log("Error listening on port " + webPort + ': ', err);
    }
    console.log((new Date()) + ': Web Server is listening on port ' + webPort + '.');
});