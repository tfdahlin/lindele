window.onload = function() {
    load_all_tracks()
    .then((data) => {
        playlist_loaded = true;
        $("#search_bar").keyup(listFilter);
        set_song_select_function();
    })
    .catch((err) => {
        console.log('Error loading playlist.');
    });

    check_login_status()
    .then((data) => {
        set_user_status(data)
        .then((data) => {
            set_header();
            add_playlist_controls();
            add_hidden_playlist_controls();
        })
        .catch((err) => {
            console.log(err);
        })
    })
    .catch((err) => {
        console.log(err);
    });
}

function set_user_status(data) {
    return new Promise((resolve, reject) => {
        curr_user_status = data;
        resolve();
    })
}