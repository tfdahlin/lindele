window.onload = function() {
    load_all_tracks()
    .then((data) => {
        playlist_loaded = true;
        console.log('Playlist load complete.');
        $("#search_bar").keyup(listFilter);
        set_song_select_function();
    })
    .catch((err) => {
        console.log('Error loading playlist.');
    });
    console.log("Page load complete.");
}