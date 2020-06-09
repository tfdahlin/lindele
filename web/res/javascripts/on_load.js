// Take care of a bunch of setup on page load, such
//  as fetching all tracks, enabling UI elements, etc
let ap;
window.onload = function() {
    ap = new AudioPlayer();
    load_all_tracks()
    .then((data) => {
        tracks_loaded = true;
        $("#search_bar").keyup(listFilter);
        set_misc_binding_functions(ap);
        ap.start();
    })
    .catch((err) => {
        console.log('Error loading playlist.');
        console.log(err);
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