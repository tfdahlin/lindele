// Take care of a bunch of setup on page load, such
//  as fetching all tracks, enabling UI elements, etc
let ap;

function get_cookie_value(name) {
    /* https://coderrocketfuel.com/article/how-to-create-read-update-and-delete-cookies-in-javascript */
    let result = document.cookie.match("(^|[^;]+)\\s*" + name + "\\s*=\\s*([^;]+)");
    if (result) {
        return result.pop();
    }
    return "";
}

function delete_cookie(name) {
    let cookie_str = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; max-age=0`;
    if (location.protocol !== 'https:') {
        document.cookie = cookie_str;
    } else {
        document.cookie = `${cookie_str}; secure`;
    }
}

function set_cookie(name, value) {
    let cookie_str = `${name}=${value}`;
    if (location.protocol !== 'https:') {
        document.cookie = cookie_str;
    } else {
        document.cookie = `${cookie_str}; secure`;
    }
}

window.onload = function() {
    // Set the flac toggle to store its status in a cookie when checked
    let flac_toggle = document.getElementById('flac-checkbox');
    flac_toggle.addEventListener('change', (event) => {
        if (event.currentTarget.checked) {
            set_cookie('flac', 'true');
        } else {
            delete_cookie('flac');
        }
    });

    // Auto-check the toggle if the cookie has been stored.
    if (get_cookie_value('flac') == 'true') {
        flac_toggle.checked = true;
    }

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