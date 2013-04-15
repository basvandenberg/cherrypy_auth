$(document).ready(function() {

    $("#register_form").submit(function(event) {

        event.preventDefault();

        var $form = $(this),
            username = $form.find('input[name="username"]').val(),
            password = $form.find('input[name="password"]').val(),
            url = $form.attr('action');

        if(password.length < 6) {
            msg = 'Password must be at least 6 characters long';
            $('#msg').html(msg);
        }
        else {
            var salt = username + document.domain;
            var salted_password = salt + password

            var hashObj = new jsSHA(salted_password, 'TEXT');
            var hashed_pw = hashObj.getHash('SHA-512','HEX');

            var posting = $.post(url, {username: username, password: hashed_pw});

            posting.done(function(data) {
                var msg = data['msg'];
                var loc = data['location'];
                if(msg) {
                    $('#msg').html(msg);
                }
                if(loc) {
                    window.location = loc;
                }
            });
        }
    });

    $("#top").focus();

});
