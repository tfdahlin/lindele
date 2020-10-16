function time_update() {
}

class AudioPlayer {
    constructor() {
        this.shuffle = true;
        this.playlist_position = 0;
        this.deck = [];
        this.deck_position = null;
        this._volume_on = true;
        this._volume = 1.0;
        this.audio_player = document.createElement('AUDIO');
        this.audio_player.id = 'audio_player';
        this.song_id = null;

        this.audio_player.addEventListener('ended', this.playNextSong.bind(this));
        this.audio_player.addEventListener('timeupdate', this.timeUpdate.bind(this));
        this.audio_player.addEventListener('playing', this.updatePlayerPlay.bind(this));
        this.audio_player.addEventListener('pause', this.updatePlayerPause.bind(this));
        this.audio_player.addEventListener('loadedmetadata', this.timeUpdate.bind(this));
        this.audio_player.addEventListener('durationchange', this.timeUpdate.bind(this));
        this.audio_player.type = 'audio/mpeg';
        this.loadVolumeSetting();
        this.updateSoundIcon(this.audio_player.volume);
        this.resizeAlbumArtwork();
        this.createBindings();
    }

    set volume(vol) {
        if (isNaN(vol)) {
            console.warn('Attempted to set volume to non-number.');
        } else {
            this._volume = vol;
        }
    }

    set volume_on(vol_on) {
        if (typeof vol_on !== 'boolean') {
            console.warn('Attempted to set on-off state to non-boolean.');
        } else {
            this._volume_on = vol_on;
        }
    }

    start() {
       // Decide what song to play first.
        if ($.urlParam('songid') == null) {
            // Fetch a random track if not songid specified.
            fetch_random_track().then((track) => {
                this.loadTrack(track);
                this.pushDeck(track).catch((err) => {
                    console.warn(err);
                })
            }).catch((err) => {
                console.log('Could not fetch initial random track.');
                console.log(err);
            })
        } else {
            // Fetch the specified track otherwise
            fetch_track_by_id($.urlParam('songid')).then((track) => {
                this.loadTrack(track);
                this.pushDeck(track).catch((err) => {
                    console.warn(err);
                })
            }).catch((err) => {
                console.log('Could not load initial track.');
            });
        } 
    }

    createBindings() {
        $("#shufflebutton").click(this.toggleShuffle.bind(this));
        $("#sharebutton").click(this.shareSong.bind(this));
        $("#previous_button").click(this.playPrevSong.bind(this));
        $("#play_button").click(this.togglePlay.bind(this));
        $("#next_button").click(this.playNextSong.bind(this));
        $("#volume_icon").click(this.toggleVolume.bind(this));
        if (navigator.mediaSession) {
            // Media key handlers.
            navigator.mediaSession.setActionHandler('previoustrack', this.playPrevSong.bind(this));
            navigator.mediaSession.setActionHandler('play', this.playAudio.bind(this));
            navigator.mediaSession.setActionHandler('pause', this.pauseAudio.bind(this));
            navigator.mediaSession.setActionHandler('nexttrack', this.playNextSong.bind(this));
        }
        $("#downloadbutton").click(this.createDownload.bind(this));

        // Handles resizing the album artwork when the window gets resized
        $(window).resize(this.resizeAlbumArtwork.bind(this));
        $("#volume_slider").on('mouseup', function() {
            $.ajax({
                type: 'POST',
                url: '{{{api_url}}}/set_volume',
                data: JSON.stringify({'volume': Math.trunc(this.value)}),
                xhrFields: {
                    withCredentials: true,
                },
            }).done((data) => {
            }).fail((err) => {
                console.log(err);
            });
        });
    }

    timeUpdate() {
        // Updates the progress bar and time display for the current track.
        var current_time = this.audio_player.currentTime;
        var total_time = this.audio_player.duration;
        var percentage = 100*(current_time / total_time);
        var progress_bar = document.getElementById("playbackprogress");
        progress_bar.style.width = percentage.toString() + "%";
        document.getElementById("playbacktimercontainer").innerHTML = (
            seconds_to_minutes(current_time) + " / " + seconds_to_minutes(total_time)
        );
    }

    seekTrackPosition(percentage) {
        var time_to_set = parseInt(percentage*this.audio_player.duration);
        if(!isFinite(time_to_set)) {
            console.warn('Non-finite time_to_set value.')
            console.warn(this.audio_player.duration);
        } else {
            this.audio_player.currentTime = time_to_set;
        }
    }

    loadVolumeSetting() {
        check_login_status()
        .then((data) => {
            if (data['user']['volume']) {
                this.audio_player.volume = data['user']['volume']/100;
                $("#volume_slider").val(data['user']['volume']);
            } else {
                this.audio_player.volume = 1.0;
                $("#volume_slider").val(100);
            }
        })
        .catch((err) => {
            console.log(err);
            this.audio_player.volume = 1.0;
            $("#volume_slider").val(100);
        })
    }

    updateSoundIcon(playervol) {
        var icon = document.getElementById("volume_icon");
        if(playervol < 0.05) {
            icon.src = "/media/very_low_volume.png";
        } else if(playervol < 0.5) {
            icon.src = "/media/low_volume.png";
        } else {
            icon.src = "/media/high_volume.png";
        }
    }

    toggleVolume() {
        // Toggle the volume on and off, and update UI as necessary.
        if(this.volume_on) {
            this.volume_on = false;
            var icon = document.getElementById("volume_icon");
            icon.src = "/media/volume_off.png";
            this.audio_player.volume = 0;
            document.getElementById("volume_slider").value = 0;
        } else {
            this.volume_on = true;
            this.audio_player.volume = volume;
            document.getElementById("volume_slider").value = volume*100;
            this.updateSoundIcon(volume);
        }
    }

    pauseAudio() {
        // Pause the audio player, and make necessary UI updates.
        var promise = this.audio_player.pause();
        // Chrome doesn't like it when you don't use the promise
        // that a call to play() or pause() returns.
        if (promise !== undefined) {
            promise.then((success) => {
                this.updatePlayerPause();
            }).catch((error) => {
                this.updatePlayerPlay();
            });
        } else {
            this.updatePlayerPause();
        }
    }

    playAudio() {
        // Play the audio player, and make necessary UI updates.
        var promise = this.audio_player.play();
        // Chrome doesn't like it when you don't use the promise
        // that a call to play() or pause() returns.
        if (promise !== undefined) {
            promise.then((success) => {
                this.updatePlayerPlay();
            }).catch((error) => {
                this.updatePlayerPause();
            })
        } else {
            this.updatePlayerPlay();
        }
    }

    updatePlayerPlay() {
        // Update the play/pause icon to play
        var icon = document.getElementById("play_button");
        icon.src = "/media/pause_button.png";
    }

    updatePlayerPause() {
        // Update the play/pause icon to pause
        var icon = document.getElementById("play_button");
        icon.src = "/media/play_button.png";
    }

    togglePlay() {
        if (this.audio_player.paused) {
            this.playAudio();
        } else {
            this.pauseAudio();
        }
    }

    toggleShuffle() {
        // Toggles shuffle and updates UI accordingly
        var shuffle_icon = document.getElementById("shufflebutton");
        if(this.shuffle) {
            this.shuffle = false;
            shuffle_icon.classList.remove("shuffle-button-on");
            shuffle_icon.classList.add("shuffle-button-off");
        } else {
            this.shuffle = true;
            shuffle_icon.classList.add("shuffle-button-on");
            shuffle_icon.classList.remove("shuffle-button-off");
        }       
    }

    playTrack(track) {
        // Loads the given track into the audio player, and updates the progress
        //  display for the track
        var track_audio_src = '{{{api_url}}}/songs/' + track['id'] + '/audio';
        if (this.checkFlacSetting()) {
            track_audio_src += '?flac=1';
        }
        this.audio_player.src = track_audio_src;
        document.getElementById("playbackprogress").style.width = "0%";
        document.getElementById("playbacktimercontainer").innerHTML = "0:00 / 0:00";

        // Autoplay it.
        this.playAudio()
    }

    setAlbumArtwork(track) {
        // Updates the album artwork display.
        var artwork_uri = '{{{api_url}}}/songs/' + track['id'] + '/artwork';
        $('#albumartwork').src = artwork_uri;
        document.getElementById("albumartwork").src = artwork_uri;
    }

    pushDeck(track) {
        return new Promise((resolve, reject) => {
            this.deck.push(track);
            this.deck_position = this.deck.length-1;
            resolve();
        });
    }

    loadTrack(track) {
        // Loads the track into out audio object, and updates the page as necessary
        this.playTrack(track);
        this.setAlbumArtwork(track);
        this.updatePageTitle(track);
        this.setTrackDetails(track);
    }

    updatePageTitle(track) {
        // Sets the page title to the current track.
        var title = track['title'];
        var artist = track['artist'];
        var page_title = title;

        if (artist) {
            page_title += ' - ' + artist;
        }
        page_title += ' | {{{service_name}}}';

        $('#page_title').html(page_title);
    }

    setTrackDetails(track) {
        $('#song-name').html(track['title']);
        this.song_id = track['id'];

        if (track['artist']) {
            $('#artist-name').html(track['artist']);
        } else {
            $('#artist-name').html("&nbsp;");
        }

        if(track['album']) {
            $('#album-name').html(track['album']);
        } else {
            $('#album-name').html("&nbsp;");
        }
    }

    playNextSong() {
        // Decide what song to play next, then load it
        this.chooseNextSong().then((track) => {
            this.loadTrack(track);
        }).catch((err) => {
            // I think this only happens if the song still
            // needs to load
            console.log(err);
        })
    }

    playPrevSong() {
        // Moves to the previous song in the deck, if it can, otherwise
        //  reload the current song.
        if(this.deck_position > 0) {
            this.deck_position -= 1;
        }
        this.loadTrack(this.deck[this.deck_position]);
    }

    createDownload() {
        var src = this.audio_player.src + '?dl=1';
        var name = document.getElementById("song-name").innerHTML;
        name = name.split('.').join('');

        // Downloads the current song.
        var link = document.createElement("a");
        link.download = name;
        link.href = src;
        document.body.appendChild(link);
        link.click();
        link.remove();
    }

    resizeAlbumArtwork() {
        // Ensure the album artwork is the right size for the sidebar.
        var album_artwork = document.getElementById("albumartwork");
        var style = window.getComputedStyle(album_artwork);
        var width = album_artwork.offsetWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight) - parseFloat(style.marginLeft) - parseFloat(style.marginRight) - parseFloat(style.borderLeft) - parseFloat(style.borderRight);
        album_artwork.style.height = parseFloat(width) + "px";
    }

    shareSong() {
        // Detect the current song playing, and copy to clipboard if it can.
        // If it can't copy to clipboard, displays the URL for sharing.
        var url = window.location.protocol;
        url += "//";
        url += window.location.hostname;
        url += "/?songid=";
        var mysongid = this.song_id;
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

    goToSong(track) {
        // Remove any track beyond current position
        while(this.deck.length > this.deck_position + 1) {
            this.deck.pop();
        }

        // If deck length is greater than 100, remove oldest element.
        if(this.deck.length > 100) {
            while(this.deck.length > 100) {
                this.deck.shift();
            }
            this.deck_position = this.deck.length - 1;
        }  

        this.pushDeck(track)
        .then((data) => {
            this.loadTrack(track);
        }).catch((err) => {
            console.log(err);
        })
    }

    chooseNextSong() {
        return new Promise((resolve, reject) => {
            // If we can proceed through the deck, do so
            if(this.deck_position < this.deck.length-1) {
                this.deck_position += 1;
                this.loadTrack(this.deck[this.deck_position]);
                resolve(this.deck[this.deck_position]);
                return;
            }

            // Remove elements from the deck if it gets longer than 100 songs.
            if(this.deck.length > 100) {
                while(this.deck.length > 100) {
                    this.deck.shift();
                }
                // Adjust the deck_position as necessary.
                this.deck_position = this.deck.length-1;
            }

            // Check if random, and choose randomly if so
            if (this.shuffle) {
                fetch_random_track().then((track) => {
                    this.pushDeck(track)
                    .then((data) => {
                        this.loadTrack(track);
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
                        if (all_tracks[i]['id'] == this.deck[this.deck_position]['id']) {
                            var next_index = (i + 1) % all_tracks.length; // Return to start if necessary.
                            next_track = all_tracks[next_index];
                            break;
                        }
                    }
                    this.pushDeck(next_track)
                    .then((data) => {
                        this.loadTrack(next_track);
                        return resolve(next_track);
                    })
                } else {
                    // If it hasn't loaded, load it and then proceed.
                    load_all_tracks()
                    .then((data) => {
                        return resolve(this.chooseNextSong());
                    })
                    .catch((err) => {
                        return reject(err);
                    });
                }
            }
        });
    }

    checkFlacSetting() {
        let flac_toggle = document.getElementById('flac-checkbox');
        return flac_toggle.checked;
    }
}

function get_track_from_id(id) {
    // Get details about a track from the tracklist based on its id.
    for (var i = 0; i < all_tracks.length; i++) {
        if (all_tracks[i]['id'] == id) {
            return all_tracks[i];
        }
    }
}

function set_misc_binding_functions(audio_player) {
    set_song_select_function(audio_player);
    set_volume_slider_function(audio_player);
    set_seek_track_position_function(audio_player);
}

function set_song_select_function(audio_player) {
    // Allows clicking of the track list to select songs.
    $("tr.track-info").click(function() {
        var rows = $('tr.track-info', hoverTable);
        var track = get_track_from_id(this.id);

        audio_player.goToSong(track);
    });
}

function set_volume_slider_function(audio_player) {
    // Updates volume on volume slider change.
    $("#volume_slider").on('input', function() {
        // Detect changes to the volume slider, and update UI as necessary.
        audio_player.audio_player.volume = this.value/100;
        volume = this.value/100;
        audio_player.updateSoundIcon(volume);
        if(audio_player.volume_on == false) {
            audio_player.volume_on = true;
        }
    })
}

function set_seek_track_position_function(audio_player) {
    // Custom seek bar
    $("#playbackcontainer").click(function(e) {
        var percentage = e.offsetX/$(this).width();
        audio_player.seekTrackPosition(percentage);
    });
}
