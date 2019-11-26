// Take care of a bunch of setup on page load, such
//  as fetching all tracks, enabling UI elements, etc
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
    // Global variable for assessing if the user is logged in or not.
    return new Promise((resolve, reject) => {
        curr_user_status = data;
        resolve();
    })
}