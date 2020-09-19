function set_header() {
    // Sets the header based on whether the user is logged in or not.
    //check_login_status().then((curr_user_status) => {
        if (curr_user_status['logged_in']) {
            set_header_logged_in()
            .then(() => {
                $('#header').html(`<div id="greeting-container" class="greeting text"><div id="greeting" class="greeting text"></div></div><div class="login-controls">
                    <a href="/profile">Profile.</a>&nbsp;<a id="logout" href="/logout">Logout.</a>`);
                if (curr_user_status['user']['admin']) {
                    let refresh_button = document.createElement('div');
                    refresh_button.innerHTML = '&nbsp;Refresh track list.';
                    refresh_button.classList.add('refresh_button')
                    refresh_button.addEventListener('click', function() {
                        $.ajax({
                            type: 'GET',
                            url: '{{{api_url}}}/refresh',
                            xhrFields: {
                                withCredentials: true,
                            },
                        });
                    })
                    $('#greeting-container').append(refresh_button);
                }
                $('#greeting').text(`Hello, ${curr_user_status['user']['username']}.`);
                $('#logout').click((e) => {
                    e.preventDefault();
                    $.ajax({
                        type: 'POST',
                        url: '{{{api_url}}}/logout',
                        xhrFields: {
                            withCredentials: true,
                        },
                    })
                    .done((data) => {
                        check_login_status()
                        .then((data) => {
                            curr_user_status = data;
                            set_header();
                        })
                        .catch((err) => {
                            console.log(err);
                        })
                    })
                    .fail((err) => {
                        console.log('Could not log out.');
                    })
                });
            })
            .catch((err) => {
                console.log(err)
            });
       } else {
            set_header_logged_out()
            .then(() => {
                $('#header').html(`
                    <div class="register-link">
                        <a href="/register">Register an account.</a>
                    </div>
                    <div class="login-form">
                        <form method="post" id="login">
                            <input type="text" placeholder="Email" name="email" autocomplete="email" required>
                            <input type="password" placeholder="Password" name="password" autocomplete="current-password" required>
                            <button type="submit" value="Submit">Login</button>
                        </form>
                    </div>
                `);
                $('#login').submit((e) => {
                    e.preventDefault();
                    data_json = {};
                    data_array = $('#login').serializeArray();
                    data_array.forEach((element) => {
                        data_json[element['name']] = element['value'];
                    });
                    $.ajax({
                        type: 'POST',
                        data: JSON.stringify(data_json),
                        url: '{{{api_url}}}/login',
                        xhrFields: {
                            withCredentials: true
                        },
                    })
                    .done((data) => {
                        if (data['status_code'] === 200) {
                            check_login_status()
                            .then((data) => {
                                curr_user_status = data;
                                set_header();
                            })
                            .catch((err) => {
                                console.log(err);
                            })
                        } else {
                            console.log('Failed to login.');
                        }
                    })
                    .fail((err) => {
                        // FAILED TO LOGIN
                        // TODO: NOTIFY USER
                        console.log('Failed to login.');
                        console.log(err);
                    });
                });
            })
            .catch((err) => {
                console.log(err);
            });
        }
}

function set_header_logged_out() {
    // Updates the header to allow sign-in
    return new Promise((resolve, reject) => {
        try {
            header_div = $('#header');
            if (header_div.hasClass('header-logged-in')) {
                header_div.removeClass('header-logged-in');
            }
            if(!header_div.hasClass('header-logged-out')) {
                header_div.addClass('header-logged-out');
            }
            resolve();
        } catch (error) {
            reject('Could not set header class.');
        }
    });
}

function set_header_logged_in() {
    // Updates the header to allow sign-out
    return new Promise((resolve, reject) => {
        try {
            header_div = $('#header');
            if (header_div.hasClass('header-logged-out')) {
                header_div.removeClass('header-logged-out');
            }
            if(!header_div.hasClass('header-logged-in')) {
                header_div.addClass('header-logged-in');
            }
            resolve();
        } catch (error) {
            reject('Coult not set header class.')
        }
    })
}

// Logout link
$("a.logoutlink").click(function() {
    window.location.href = "logout";
});