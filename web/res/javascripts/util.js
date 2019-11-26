var all_tracks = [];
var tracks_loaded = false;
var curr_user_status = {};

$.ajaxSetup({
    crossDomain: true,
    xhrFields: {
        withCredentials: true,
    },
});

function escape_string(input_string) {
    // Escapes a string for inside HTML
    var tagsToReplace = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    };
    return input_string.replace(/[&<>"'\/]/g, function(tag) {
        return tagsToReplace[tag] || tag;
    });
}

function check_login_status() {
    // Checks if the user is logged in with the API.
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: 'https://api.music.acommplice.com/current_user',
            xhrFields: {
                withCredentials: true,
            },
        })
        .done(function(data) {
            if (data['status_code'] === 200) {
                resolve(data['data']);
            } else {
                reject('Failed to check login status.');
            }
        })
        .fail((err) => {
            reject(err);
        });
    });
}

function load_all_tracks() {
    // Fetch tracks for the current playlist, and load them into the window.
    return new Promise((resolve, reject) => {
        // "You're listening to <playlist name by owner / Acommplice music>. (X tracks)"
        set_playlist_info_text();

        // Cache all the tracks that we've loaded into all_tracks.
        fetch_tracks()
        .then((tracks) => {
            all_tracks = tracks;
            tracks_loaded = true;
            var track_count_div = $("#track-count");
            track_count_div.html("(" + tracks.length + " tracks)");
            populate_playlist(tracks);
            resolve();
        })
        .catch((err) => {
            track_count_div.html("(0 tracks)");
            reject('Could not fetch tracks.');
        });
    });
}

function _fetch_all_tracks() {
    // Fetches track info for all songs.
    return new Promise((resolve, reject) => {
        $.get('https://api.music.acommplice.com/songs')
        .done(function(data) {
            if (data['status_code'] === 200) {
                resolve(data['data']['tracks']);
            } else {
                reject('Failed to fetch all tracks.');
            }
        })
        .fail((err) => {
            reject(err);
        });
    });
}

function fetch_tracks_from_playlist(playlistid) {
    // Fetches track info for the given playlist.
    return new Promise((resolve, reject) => {
        $.get('https://api.music.acommplice.com/playlists/' + playlistid)
        .done((data) => {
            if (data['status_code'] === 200) {
                resolve(data['data']['tracks']);
            } else {
                reject();
            }
        })
        .fail((err) =>{
            reject();
        });
    });
}

function fetch_tracks() {
    // Decide whether to get playlist track info, or all track info,
    //  and return results accordingly.
    return new Promise((resolve, reject) => {
        // First check if we're loading a playlist or all songs.
        var param = $.urlParam('playlistid');
        if(param == null) { // If it's not a playlist
            _fetch_all_tracks()
            .then((tracks) => {
                resolve(tracks);
            })
            .catch((err) => {
                reject();
            });
        } else {
            fetch_tracks_from_playlist(param)
            .then((tracks) => {
                resolve(tracks);
            })
            .catch((err) => {
                _fetch_all_tracks()
                .then((tracks) => {
                    resolve(tracks);
                })
                .catch((err) => {
                    reject();
                });
            });
        }
    });
}

function fetch_track_by_id(id) {
    // Fetch track info for a specific track
    return new Promise((resolve, reject) => {
        $.get('https://api.music.acommplice.com/songs/' + id)
        .done(function(data) {
            if (data['status_code'] == 200) {
                resolve(data['data']);
            } else {
                reject();
            }
        })
        .fail(function() {
            reject();
        });
    });
}

function fetch_random_track() {
    // Select a random track, and return its track info.
    return new Promise((resolve, reject) =>{
        if (tracks_loaded) {
            var track_num = Math.floor(Math.random() * all_tracks.length);
            resolve(all_tracks[track_num]);
        } else {
            load_all_tracks()
            .then((data) => {
                var track_num = Math.floor(Math.random() * all_tracks.length);
                resolve(all_tracks[track_num]);
            })
            .catch((err) => {
                reject(err);
            });
        }
    });
}

function set_playlist_info_text() {
    // Display playlist info above track info.

    // Text that we're modifying.
    var playlist_info_div = $('#playlist-info');

    // Extract the playlistid parameter.
    var page_url = window.location.search.substring(1);
    var url_vars = page_url.split('&');

    var playlist_id;

    for (var param of url_vars) {
        var param_name = param.split('=');
        if (param_name[0] === 'playlistid') {
            playlist_id = param_name[1];
        }
    }

    if (playlist_id) {
        $.ajax({
            type: 'GET',
            url: 'https://api.music.acommplice.com/playlists/' + playlist_id,
            xhrFields: {
                withCredentials: true,
            },
        })
        .done((data) => {
            playlist_info_div.html(`You're listening to ${escape_string(data['data']['name'])} by ${escape_string(data['data']['owner_name'])}`);
        })
        .fail((err) => {
            console.log(err);
        })
    }
    else {
        playlist_info_div.html("You're listening to all songs.");
    }
}

function populate_playlist(tracks) {
    // Creates the track list table.
    var container = $('#playlist-content');
    container.html(`
        <table id="hoverTable" class="hoverTable">
            <tr class="text table-header-tr" id="header-row">
                <th width="50%">Song name</th>
                <th width="25%">Artist</th>
                <th width="20%">Album</th>
                <th width="5%">Length</th>
            </tr>
        </table>
    `);
    var table = $('#hoverTable');
    var track_no = 0;
    var i;
    for (i=0; i < tracks.length; i++) {
        var track = tracks[i];
        var track_id = track['id'];
        var track_title = track['title'];
        if (!track_title) {
            continue;
        }
        var track_artist = track['artist'];
        if (!track_artist) {
            track_artist = '';
        }
        var track_album = track['album'];
        if (!track_album) {
            track_album = '';
        }
        var track_length = track['length'];
        if (!track_length) {
            continue;
        }
        var row_type;
        if (track_no % 2 === 0) {
            row_type = 'evenrow';
        } else {
            row_type = 'oddrow';
        }
        table.append(
            '<tr id="' + track_id + '" class="' + row_type + ' track-info text">' +
                '<td id="' + track_id + '" class="track-info" width="50%">' + track_title + '</td>' +
                '<td id="' + track_id + '" class="track-info" width="25%">' + track_artist + '</td>' +
                '<td id="' + track_id + '" class="track-info" width="20%">' + track_album + '</td>' +
                '<td id="' + track_id + '" class="track-info" width="5%">' + track_length + '</td>' +
            '</tr>'
        )
        track_no += 1;
    }
}

function updateSoundIcon(playervol) {
    var icon = document.getElementById("volume_icon");
    if(playervol < 0.05) {
        icon.src = "/media/very_low_volume.png";
    } else if(playervol < 0.5) {
        icon.src = "/media/low_volume.png";
    } else {
        icon.src = "/media/high_volume.png";
    }
}

function seconds_to_minutes(seconds) {
    // Converts raw seconds into a more human-readable form for display
    var hours = parseInt(seconds/3600);
    var minutes = parseInt((seconds % 3600)/60);
    var seconds = parseInt((seconds % 60));
    var result = "";
    if(hours > 0) {
        result += hours.toString() + ":";
    } 
    if(minutes > 0) {
        if(minutes >= 10) {
            result += parseInt(minutes/10).toString();
        }
        result += (minutes%10).toString() + ":";
    } else {
        result += "0:";
    }
    if(!isNaN(seconds/10) && !isNaN(seconds %10)) {
        result += parseInt(seconds/10) + (seconds%10).toString();
    } else if(!isNaN(seconds/10)) {
        result += "0" + (seconds%10).toString();
    } else {
        result += "00";
    }
    return result;
}

function update_player_play() {
    // Update the play/pause icon to play
    var icon = document.getElementById("play_button");
    icon.src = "/media/pause_button.png";
    onplaying = true;
    onpause = false;
}

function update_player_pause() {
    // Update the play/pause icon to pause
    var icon = document.getElementById("play_button");
    icon.src = "/media/play_button.png";
    onplaying = false;
    onpause = true;
}

function listFilter() {
    // Filters the track list based on the search bar
    var punctRE = /[\u2000-\u206F\u2E00-\u2E7F\\'!"#$%&()*+,\-.\/:;<=>?@\[\]^_`{|}~]/g;
    var spaceRE = /\s+/g;
    var substring = document.getElementById('search_bar').value.toLowerCase();
    substring = substring.replace(punctRE, '').replace(spaceRE, ' ');
    var table = document.getElementById('hoverTable');
    if (!table) {
        return;
    }
    for(var i=1;i<table.rows.length;i++) {
        var title = table.rows[i].cells[0].textContent.toLowerCase().replace(punctRE, '').replace(spaceRE, ' ');
        var artist = table.rows[i].cells[1].textContent.toLowerCase().replace(punctRE, '').replace(spaceRE, ' ');
        var album = table.rows[i].cells[2].textContent.toLowerCase().replace(punctRE, '').replace(spaceRE, ' ');
        if( !title.includes(substring) &&
            !artist.includes(substring) &&
            !album.includes(substring)) {
            table.rows[i].style.display = 'none';
        } else {
            table.rows[i].style.display = '';
        }

    }
}

// Thank you sitepoint.com
// $.urlParam('parameter_name') returns parameter value
$.urlParam = function(name) {
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if(results == null) {
        return null;
    } else {
        return results[1] || 0;
    }
}