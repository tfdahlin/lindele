function time_update() {
    // Updates the progress bar and time display for the current track.
    var current_time = audio_player.currentTime;
    var total_time = audio_player.duration;
    var percentage = 100*(current_time / total_time);
    var progress_bar = document.getElementById("playbackprogress");
    progress_bar.style.width = percentage.toString() + "%";
    document.getElementById("playbacktimercontainer").innerHTML = seconds_to_minutes(current_time) + " / " + seconds_to_minutes(total_time);
}

var shuffle = true;
var playlist_position = 0;
var deck = []; // This is a list of tracks, not ids.
var deck_position = null; // Integer position in the deck.
var volume = 1.0;
var volume_on = true;

var audio_player = document.createElement('AUDIO');

audio_player.id = 'audio_player';
audio_player.addEventListener('ended', play_next_song);
audio_player.addEventListener('timeupdate', time_update);
audio_player.addEventListener('playing', update_player_play);
audio_player.addEventListener('pause', update_player_pause);
audio_player.addEventListener('loadedmetadata', time_update);
audio_player.addEventListener('durationchange', time_update);
audio_player.type = 'audio/mpeg';
audio_player.volume = document.getElementById('volume_slider').value/100;
updateSoundIcon(audio_player.volume);

// Decide what song to play first.
if ($.urlParam('songid') == null) {
    // Fetch a random track if not songid specified.
    fetch_random_track().then((track) => {
        load_track(track);
        deck.push(track);
        deck_position = deck.length-1;
    }).catch((err) => {
        console.log('Could not fetch initial random track.');
        console.log(err);
    })
} else {
    // Fetch the specified track otherwise
    fetch_track_by_id($.urlParam('songid')).then((track) => {
        load_track(track);
        deck.push(track);
        deck_position = deck.length-1;
    }).catch((err) => {
        console.log('Could not load initial track.');
    });
}

function load_track(track) {
    // Loads the track into out audio object, and updates the page as necessary
    play_track(track);
    set_album_artwork(track);
    update_page_title(track);
    set_track_details(track);
}

function play_track(track) {
    // Loads the given track into the audio player, and updates the progress
    //  display for the track
    var track_audio_src = '{{{api_url}}}/songs/' + track['id'] + '/audio';
    audio_player.src = track_audio_src;
    document.getElementById("playbackprogress").style.width = "0%";
    document.getElementById("playbacktimercontainer").innerHTML = "0:00 / 0:00";

    // Autoplay promise stuff for Chrome to not yell at me in the console lol
    var promise = audio_player.play();
    if (promise !== undefined) {
        promise.then( (success) => {
            update_player_play();
        }).catch((error) => {
            update_player_pause();
        });
    } 
}

function set_album_artwork(track) {
    // Updates the album artwork display.
    var artwork_uri = '{{{api_url}}}/songs/' + track['id'] + '/artwork';
    $('#albumartwork').src = artwork_uri;
    document.getElementById("albumartwork").src = artwork_uri;
}

function update_page_title(track) {
    // Sets the page title to the current track.
    var title = track['title'];
    var artist = track['artist'];
    var page_title = '';

    if (artist) {
        page_title = title + ' - ' + artist + ' | Music';
    } else {
        page_title = title + ' | Music';
    }

    $('#page_title').html(page_title);
}

function set_track_details(track) {
    // Updates the track details section of the sidebar.
    var title = track['title'];
    var artist = track['artist'];
    var album = track['album'];
    var songid = track['id'];
    $('#song-name').html(title);
    $('#song_id').html(songid);

    if (artist) {
        $('#artist-name').html(artist);
    } else {
        $('#artist-name').html("&nbsp;");
    }

    if(album) {
        $('#album-name').html(album);
    } else {
        $('#album-name').html("&nbsp;");
    }
}

function play_next_song() {
    // Decide what song to play next.
    choose_next_song().then((track) => {
        load_track(track);
    }).catch((err) => {
        // This only really happens when the song still needs to load.
    })
}

function push_track(track) {
    // Adds the track to the deck.
    return new Promise((resolve, reject) => {
        deck.push(track);
        deck_position = deck.length-1;
        resolve();
    })
}

function choose_next_song() {
    // Select the next song to play
    return new Promise((resolve, reject) => {
        // If we can proceed through the deck, do so
        if(deck_position < deck.length-1) {
            deck_position += 1;
            load_track(deck[deck_position]);
            resolve(deck[deck_position]);
            return;
        }

        // Remove elements from the deck if it gets longer than 100 songs.
        if(deck.length > 100) {
            while(deck.length > 100) {
                deck.shift();
            }
            // Adjust the deck_position as necessary.
            deck_position = deck.length-1;
        }

        // Check if random, and choose randomly if so
        if (shuffle) {
            fetch_random_track().then((track) => {
                push_track(track)
                .then((data) => {
                    load_track(track);
                    return resolve(track);
                })
            }).catch((err) => {
                return reject(err);
            })
        } else {
            // Make sure that the track list has loaded
            if (tracks_loaded) {
                // Select the next track in track_list.
                // Current track is deck[deck_position]
                // Iterate through track_list til we find a matching id
                var next_track;
                for (var i = 0; i < all_tracks.length; i++) {
                    if (all_tracks[i]['id'] == deck[deck_position]['id']) {
                        var next_index = (i + 1) % all_tracks.length; // Return to start if necessary.
                        next_track = all_tracks[next_index];
                        break;
                    }
                }
                push_track(next_track)
                .then((data) => {
                    load_track(next_track);
                    return resolve(next_track);
                })
            } else {
                // If it hasn't loaded, load it and then proceed.
                load_all_tracks()
                .then((data) => {
                    return resolve(choose_next_song());
                })
                .catch((err) => {
                    return reject(err);
                });
            }
        }

    });
    
}

function play_audio() {
    // Play the audio player, and make necessary UI updates.
    var promise = audio_player.play();
    if (promise !== undefined) {
        promise.then( (success) => {
            update_player_play();
        }).catch((error) => {
            update_player_pause();
        });
    }
}

function pause_audio() {
    // Pause the audio player, and make necessary UI updates.
    var promise = audio_player.pause();
    if (promise !== undefined) {
        promise.then((success) => {
            update_player_pause();
        }).catch((error) => {
            update_player_play();
        });
    }
}

function toggle_play() {
    // Toggle the audio player.
    if(audio_player.paused) {
        play_audio();
    } else {
        pause_audio();
    }
}

$("#volume_slider").on('input', 
    function() {
        // Detect changes to the volume slider, and update UI as necessary.
        audio_player.volume = this.value/100;
        volume = this.value/100;
        updateSoundIcon(volume);
        if(volume_on == false) {
            volume_on = true;
        }
    });


function toggle_volume() {
    // Toggle the volume on and off, and update UI as necessary.
    if(volume_on) {
        volume_on = false;
        var icon = document.getElementById("volume_icon");
        icon.src = "/media/volume_off.png";
        audio_player.volume = 0;
        document.getElementById("volume_slider").value = 0;
    } else {
        volume_on = true;
        audio_player.volume = volume;
        document.getElementById("volume_slider").value = volume*100;
        updateSoundIcon(volume);
    }
}

function play_prev_song() {
    // Moves to the previous song in the deck, if it can, otherwise
    //  reload the current song.
    if(deck_position > 0) {
        deck_position -= 1;
    }
    load_track(deck[deck_position]);
}

function resize_album_artwork() {
    // Ensure the album artwork is the right size for the sidebar.
    var album_artwork = document.getElementById("albumartwork");
    var style = window.getComputedStyle(album_artwork);
    var width = album_artwork.offsetWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight) - parseFloat(style.marginLeft) - parseFloat(style.marginRight) - parseFloat(style.borderLeft) - parseFloat(style.borderRight);
    album_artwork.style.height = parseFloat(width) + "px";
}

function share_song() {
    // Detect the current song playing, and copy to clipboard if it can.
    // If it can't copy to clipboard, displays the URL for sharing.
    var url = window.location.protocol;
    url += "//";
    url += window.location.hostname;
    url += "/?songid=";
    var mysongid = document.getElementById("song_id").textContent;
    url += mysongid;
    if(window.clipboardData && window.clipboardData.setData) {
        return clipboardData.setData("Text", url);
    } else if(document.queryCommandSupported && document.queryCommandSupported("copy")) {
        var textarea = document.createElement("textarea");
        textarea.textContent = url;
        textarea.style.position = "fixed";
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand("copy");
            alert("Link copied to clipboard!");
            return;
        } catch (ex) {
            console.warn("Copy to clipboard failed.", ex);
            window.prompt("Copy to clipboard: Ctrl+C or Cmd+C, Enter", text);
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function toggle_shuffle() {
    // Toggles shuffle and updates UI accordingly
    var shuffle_icon = document.getElementById("shufflebutton");
    if(shuffle) {
        shuffle = false;
        shuffle_icon.classList.remove("shuffle-button-on");
        shuffle_icon.classList.add("shuffle-button-off");
    } else {
        shuffle = true;
        shuffle_icon.classList.add("shuffle-button-on");
        shuffle_icon.classList.remove("shuffle-button-off");
    }
}

function downloadFile(uri, name) {
    // Downloads the current song.
    var link = document.createElement("a");
    link.download = name;
    link.href = uri;
    document.body.appendChild(link);
    link.click();
    link.remove();
}

// Handles resizing the album artwork when the window gets resized
resize_album_artwork();
$(window).resize(resize_album_artwork);

// Logout link
$("a.logoutlink").click(function() {
    window.location.href = "logout";
});

// This is the audio navigation thing
$("#playbackcontainer").click(function(e) {
    var percentage = e.offsetX/$(this).width();
    var time_to_set = parseInt(percentage*audio_player.duration);
    if(!isFinite(time_to_set)) {
        console.warn('Non-finite time_to_set value.')
        console.warn(audio_player.duration);
    } else {
        audio_player.currentTime = time_to_set;
    }
});

$("#shufflebutton").click(toggle_shuffle);
$("#sharebutton").click(share_song);
$("#previous_button").click(play_prev_song);
$("#play_button").click(toggle_play);
$("#next_button").click(play_next_song);
$("#volume_icon").click(toggle_volume);
if (navigator.mediaSession) {
    // Media key handlers.
    navigator.mediaSession.setActionHandler('previoustrack', play_prev_song);
    navigator.mediaSession.setActionHandler('play', play_audio);
    navigator.mediaSession.setActionHandler('pause', pause_audio);
    navigator.mediaSession.setActionHandler('nexttrack', play_next_song);
}
$("#downloadbutton").click(function() {
    var src = audio_player.src;
    var name = document.getElementById("song-name").innerHTML;
    name = name.split('.').join('');
    downloadFile(src, name);
});

$("#volume_slider").on('mouseup', function() {
    $.ajax({
        type: 'POST',
        url: '{{{api_url}}}/set_volume',
        data: JSON.stringify({'volume': Math.trunc(this.value)}),
        xhrFields: {
            withCredentials: true,
        },
    })
    .done((data) => {
    })
    .fail((err) => {
        console.log(err);
    });
});

function get_track_from_id(id) {
    // Get details about a track from the tracklist based on its id.
    for (var i = 0; i < all_tracks.length; i++) {
        if (all_tracks[i]['id'] == id) {
            return all_tracks[i];
        }
    }
}

function set_song_select_function() {
    // Allows clicking of the track list to select songs.
    $("tr.track-info").click(function() {
        var rows = $('tr.track-info', hoverTable);

        // Remove anything from the deck beyond our current position
        while(deck.length > deck_position + 1) {
            deck.pop();
        }

        // If deck length is greater than 100, then remove the oldest element.
        if(deck.length > 100) {
            while(deck.length > 100) {
                deck.shift();
            }
            deck_position = deck.length - 1;
        }

        var track = get_track_from_id(this.id);

        push_track(track)
        .then((data) => {
            load_track(track);
        })
        .catch((err) => {
            console.log(err);
        });
    });
}

function set_initial_volume() {
    // Loads user volume settings, and sets accordingly.
    check_login_status()
    .then((data) => {
        if (data['user']['volume']) {
            audio_player.volume = data['user']['volume']/100;
            $("#volume_slider").val(data['user']['volume']);
        }
    })
    .catch((err) => {
        console.log(err);
    })
}
set_initial_volume();