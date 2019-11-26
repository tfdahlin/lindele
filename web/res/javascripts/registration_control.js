// Instead of actually going to a URL, we want to handle this in the window.
$('#register').submit((e) => {
    e.preventDefault();
    data_json = {};
    data_array = $('#register').serializeArray();
    data_array.forEach((element) => {
        data_json[element['name']] = element['value'];
    });
    console.log(JSON.stringify(data_json));
    $.post('https://api.music.acommplice.com/register', data=JSON.stringify(data_json))
    .done((data) => {
        if (data['status_code'] === 200) {
            window.location.href = "/";
        } else {
            reject('Failed to check login status.');
        }
    })
    .fail((err) => {
        // FAILED TO LOGIN
        // TODO: NOTIFY USER
        console.log(err);
    });
});