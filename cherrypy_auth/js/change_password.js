$(document).ready(function() {

    $("#change_password_form").submit(function(event) {

        event.preventDefault();

        var $form = $(this),
            password_old = $form.find('input[name="password_old"]').val(),
            password_new = $form.find('input[name="password_new"]').val(),
            username = $form.find('input[name="username"]').val().toLowerCase(),
            url = $form.attr('action');

        if(password_new.length < 6) {
            msg = 'Password must be at least 6 characters long';
            $('#msg').html(msg);
        }
        else {
            var salt = username + document.domain;

            var salted_password_old = salt + password_old;
            var salted_password_new = salt + password_new;

            var hashObj_old = new jsSHA(salted_password_old, 'TEXT');
            var hashed_pw_old = hashObj_old.getHash('SHA-512','HEX');
            
            var hashObj_new = new jsSHA(salted_password_new, 'TEXT');
            var hashed_pw_new = hashObj_new.getHash('SHA-512','HEX');

            var posting = $.post(url, {password_old: hashed_pw_old, 
                                       password_new: hashed_pw_new});

            posting.done(function(data) {
                var msg = data['msg'];
                var loc = data['location'];
                if(msg) {
                    $('#msg').html(msg);
                }
                if(loc) {
                    setTimeout(
                        function() {
                            window.location = loc;
                        }, 1500);
                }
            });
        }
    });

    $("#top").focus();

});
