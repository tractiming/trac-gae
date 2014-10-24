// This setup function handles the csrf authentication. It reads the csrf
// cookie and sets ajax to automatically add the token to each header. For
// reference, see: http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request 
$.ajaxSetup({ 
     beforeSend: function(xhr, settings) {
         function getCookie(name) {
             var cookieValue = null;
             if (document.cookie && document.cookie != '') {
                 var cookies = document.cookie.split(';');
                 for (var i = 0; i < cookies.length; i++) {
                     var cookie = jQuery.trim(cookies[i]);
                     // Does this cookie string begin with the name we want?
                 if (cookie.substring(0, name.length + 1) == (name + '=')) {
                     cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                     break;
                 }
             }
         }
         return cookieValue;
         }
         if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
             // Only send the token to relative URLs i.e. locally.
             xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
         }
     } 
});

$(document).ready(function() {

    $("#add_err").css('display', 'none', 'important');
    $("#dropdown_text").text("Login");
    
    // Control of the login box.
    var button = $('#loginButton');
    var box = $('#loginBox');
    var form = $('#loginForm');
    button.removeAttr('href');
    button.mouseup(function(login) {
        box.toggle();
        button.toggleClass('active');
    });
    form.mouseup(function() { 
        return false;
    });
    $(this).mouseup(function(login) {
        if(!($(login.target).parent('#loginButton').length > 0)) {
            button.removeClass('active');
            box.hide();
        }
    });
    
    // Login functionality.
    $("#login").click(function(){

       // Get the username and password from login form.
       var username=$('input[id=username]').val();
       var password=$('input[id=password]').val();

       // Send a POST to the api to request an access token.
       $.ajax({
           type: "POST",
           url: "/oauth2/access_token/",
           data: {
               username: username,
               password: password,
               grant_type: 'password',
               client_id: username,
           },
          
           // Login was successful.
           success: function(data) {
                   var access_token = data.access_token;
                    $("#dropdown_text").text(username);
                    $("#loginBox").html('<form id="loginForm"><span><a href="#">My Profile</a></span><br><span><a href="#">Logout</a></span></form>');
                    button.removeClass('active');
                    box.hide();
           },

           // Login request failed.
           error: function(xhr, errmsg, err) {
               alert("Invalid login.");
           }
       });

       return false;

   });

   $("#register").click(function(){

       // Get the username and password from registration form.
       var username=$('input[id=name]').val();
       var password=$('input[id=word]').val();
       var user_type=$('input[id=utype]:checked').val();

       alert(username);
       // Send a POST to the api to register the user.
       $.ajax({
           type: "POST",
           url: "/api/register/",
           data: {
               username: username,
               password: password,
               user_type: user_type,
           },
          
           // Registration was successful.
           success: function(data) {
                   alert("Registered sucessfully");
           },

           // Registration failed.
           error: function(xhr, errmsg, err) {
               alert(user_type);
               alert("Invalid registration.");
           }
       });

       return false;

   });
});


function get_session_resultsl(access_token, session_num, success_callback) {
    $.ajax({
        type: "GET",
        url: "/api/sessions/"+session_num.toString()+"/",
        data

    });
}

