$(document).ready(function() {

    $("#forgot_password_form").submit(function(event) {

        event.preventDefault();

        var $form = $(this),
            username = $form.find('input[name="username"]').val(),
            url = $form.attr('action');

        var posting = $.post(url, {username: username});

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
    });

    $("#single").focus();

});
