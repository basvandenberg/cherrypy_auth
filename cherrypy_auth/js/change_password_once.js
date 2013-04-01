$(document).ready(function() {

    $("#change_password_once_form").submit(function(event) {

        event.preventDefault();

        // obtain get parameters
        var $_GET = {};
        document.location.search.replace(/\??(?:([^=]+)=([^&]*)&?)/g, function () {
            function decode(s) {
                return decodeURIComponent(s.split("+").join(" "));
            }

            $_GET[decode(arguments[1])] = decode(arguments[2]);
        });

        //var url_parts = window.location.pathname.split("/").reverse();
        //var token = url_parts[0]
        //var username = url_parts[1]
        var token = $_GET['token'];
        var username = $_GET['username'];

        var $form = $(this),
            password = $form.find('input[name="password"]').val(),
            url = $form.attr('action');

        var salt = username + document.domain;
        var salted_password = salt + password

        var hashObj = new jsSHA(salted_password, 'TEXT');
        var hashed_pw = hashObj.getHash('SHA-512','HEX');

        var posting = $.post(url, {username: username, token: token,
                password: hashed_pw});

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
