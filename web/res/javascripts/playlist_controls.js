function add_playlist_controls() {
    $.ajax({
        type: 'GET',
        url: 'https://api.music.acommplice.com/playlists',
        xhrFields: {
            withCredentials: true
        },
    })
    .done((data) => {
        if (data['status_code'] === 200) {
            playlists = data['data']['playlists'];
            num_playlists = playlists.length;
            if (num_playlists > 0) {
                $('#playlist-controls').append(`
                    <div class="select-playlist">
                        <select id="playlistoptions" class="playlist-dropdown">
                            <option value="0">All songs</option>
                        </select>
                        <button class="go-to-playlist" id="go_to_playlist_button" type="button">Go to playlist</button>
                    </div>
                `);
                playlists.forEach((element) => {
                    option_html = `
                        <option value="${element['id']}">
                            ${element['owner_name'].escape()}: ${element['name'].escape()}
                        </option>
                    `;
                    $('#playlistoptions').append(option_html);
                });
                $("#go_to_playlist_button").click(go_to_playlist);
            }
        }
        else {
            console.log('Error while accessing playlists.');
        }
    })
    .fail((data) => {
        console.log('Could not fetch playlists.');
    })
    .always((data) => {
        // Set up create-playlist button, if the user is logged in..    
        if (curr_user_status['logged_in']) {
            $('#playlist-controls').append(`
                <div class="create-playlist">
                    <button id="new_playlist_button" class="create-playlist-button" type="button">New Playlist</button>
                </div>
            `);
            $("#new_playlist_button").click(request_playlist_name);
        }
    });
}

function get_owned_playlists() {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: 'GET',
            url: `https://api.music.acommplice.com/playlists/owned`,
            xhrFields: {
                withCredentials: true,
            },
        })
        .done((data) => {
            resolve(data['data']);
        })
        .fail((err) => {
            reject(err);
        })
    })
}

function add_hidden_playlist_controls() {
    if (curr_user_status['logged_in']) {
        get_owned_playlists()
        .then((playlists) => {
            playlists = playlists['playlists']
            if(playlists.length < 1) {
                console.log('No playlists.');
                return;
            }
            $('#body').append(`
                <div class="hide text" id="rmenu">
                    <table id="playlist-table">

                    </table>
                </div>
            `);
            if ($.urlParam('playlistid')) {
                playlists.forEach((playlist) => {
                    if (playlist['id'] == $.urlParam('playlistid')) {
                        $('#playlist-table').append(`
                            <tr style="background-color: #cc2233" id="removetrack">
                                <td id="${playlist['id']}" class="removetrack">
                                    Remove song from ${playlist['name'].escape()}
                                </td>
                            </tr>
                        `);
                    }
                })
                $("td.removetrack").click(function() {
                    var playlist = this.id;
                    remove_song_from_playlist(playlist, rc_song_id);
                });
            }

            $('#playlist-table').append(`
                <tr class="text" style="background-color: $1818181;" id="rmenu-header-row">
                    <th>Add song to playlist</th>
                </tr>
            `);
            playlists.forEach((playlist, id) => {
                var row_type;
                if (id % 2 == 0) {
                    row_type = 'evenrow';
                } else {
                    row_type = 'oddrow';
                }
                $('#playlist-table').append(`
                    <tr class="${row_type} playlist text">
                        <td id="${playlist['id']}" class="playlist">
                            ${playlist['name'].escape()}
                        </td>
                    </tr>
                `)
            });

            $("td.playlist").click(function() {
                var playlist = this.id;
                add_song_to_playlist(playlist, rc_song_id);
            });
            bind_playlist_menu();
        })
        .catch((err) => {
            console.log(err);
        });
    }
}

var rc_song_id = 0;


function mouseX(evt) {
    if (evt.pageX) {
        return evt.pageX;
    } else if (evt.clientX) {
       return evt.clientX + (document.documentElement.scrollLeft ?
           document.documentElement.scrollLeft :
           document.body.scrollLeft);
    } else {
        return null;
    }
}

function mouseY(evt) {
    if (evt.pageY) {
        return evt.pageY;
    } else if (evt.clientY) {
       return evt.clientY + (document.documentElement.scrollTop ?
       document.documentElement.scrollTop :
       document.body.scrollTop);
    } else {
        return null;
    }
}

function bind_playlist_menu() {
    if (document.addEventListener) { // IE >= 9; other browsers
        document.addEventListener('contextmenu', function(e) {
            //alert("You've tried to open context menu"); //here you draw your own menu
            if($(e.target).hasClass("track-info")) {
                e.preventDefault();

                document.getElementById("rmenu").className = "show";
                document.getElementById("rmenu").style.top =  mouseY(e) + 'px';
                document.getElementById("rmenu").style.left = mouseX(e) + 'px';
                rc_song_id = e.target.id;
                $(document).bind("click", function(event) {
                    document.getElementById("rmenu").className = "hide";
                    $(document).unbind("click", function(event) {
                    });
                });
            }
        }, false);
    }
}

function add_song_to_playlist(playlist_id, rc_song_id) {
    json_data = JSON.stringify({'songid': rc_song_id});
    $.ajax({
        type: 'POST',
        url: `https://api.music.acommplice.com/playlists/${playlist_id}/add`,
        xhrFields: {
            withCredentials: true,
        },
        data: json_data,
    })
    .done((data) => {
        console.log(data);
    })
    .fail((err) => {
        console.log(err);
    });
}

function remove_song_from_playlist(playlist_id, rc_song_id) {
    json_data = JSON.stringify({'songid': rc_song_id})
    $.ajax({
        type: 'POST',
        url: `https://api.music.acommplice.com/playlists/${playlist_id}/remove`,
        xhrFields: {
            withCredentials: true,
        },
        data: json_data,
    })
    .done((data) => {
        // TODO :reload playlist
    })
    .fail((err) => {
        console.log(err);
    })
}

function request_playlist_name() {
    var new_playlist_name = prompt("Create a new playlist", "Playlist name");

    if(new_playlist_name == null || new_playlist_name == "") {
        return;
    }
    json_data = JSON.stringify({'playlist_name': new_playlist_name})

    $.ajax({
        type: 'POST',
        url: `https://api.music.acommplice.com/playlists/create`,
        xhrFields: {
            withCredentials: true,
        },
        data: json_data,
    })
    .done((data) => {
        // TODO :reload list of playlists.
    })
    .fail((err) => {
        console.log(err);
    })
}


function go_to_playlist() {
    var decision = document.getElementById("playlistoptions");
    if(decision.value== "0")
    {
        window.location.href='/';
    } else {
        window.location.href = "/?playlistid=" + decision.options[decision.selectedIndex].value;
    }
}