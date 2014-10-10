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
   $("#login").click(function(){

       // Get the username and password from login form.
       var username=$('input[id=name]').val();
       var password=$('input[id=word]').val();

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
               alert("trying");
                   var access_token = data.access_token;
                   alert("Logged in sucessfully");
           },

           // Login request failed.
           error: function(xhr, errmsg, err) {
               alert("Invalid login.");
           }
       });

       return false;

   });
});
