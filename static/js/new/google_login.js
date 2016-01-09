var googleUser = {};
var startApp = function() {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({
            client_id: '983021202491-kupk29qejvri4mlpd8ji0pa7r31bkrin.apps.googleusercontent.com',
            cookiepolicy: 'single_host_origin',
        });
        attachSignin(document.getElementById('google-sign-in'));
    });
};

function attachSignin(element) {
    console.log(element.id);
    auth2.attachClickHandler(element, {}, function(googleUser) {
        var id_token = googleUser.getAuthResponse().id_token;
        var client_id = '983021202491-kupk29qejvri4mlpd8ji0pa7r31bkrin.apps.googleusercontent.com';
        var email = googleUser.getBasicProfile().getEmail();
        var data = {
            id_token: id_token,
            google_client_id: client_id,
            trac_client_id: 'aHD4NUa4IRjA1OrPD2kJLXyz34c06Bi5eVX8O94p', 
            email: email
        };
        $.ajax({
            type: 'POST',
            url: '/google-auth/',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(data) {
                var access_token = data.access_token;
                var user_type = data.user.user_type;
                sessionStorage.setItem('access_token', access_token);
                sessionStorage.setItem('usertype', user_type);
                location.href = '/home';
            },
            error: function(xhr, errmsg, err){
                alert('something went wrong');
            }
        });
    }, function(error) {
        alert(JSON.stringify(error, undefined, 2));
    });
}
