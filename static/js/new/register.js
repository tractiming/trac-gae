$(function() {

  // initialize spinner
  var opts = {
    lines: 13,              // The number of lines to draw
    length: 28,             // The length of each line
    width: 14,              // The line thickness
    radius: 42,             // The radius of the inner circle
    scale: 0.3,             // Scales overall size of the Spinner
    corners: 1,             // Corner roundness (0..1)
    color: '#3577a8',       // #rgb or #rrggbb or array of colors
    opacity: 0.25,          // Opacity of the lines
    rotate: 0,              // The rotation offset
    direction: 1,           // 1: clockwise, -1: counterclockwise
    speed: 1,               // Rounds per second
    trail: 60,              // Afterglow percentage
    fps: 20,                // Frames per second when using setTimeout() as a fallback for CSS
    zIndex: 1,              // The z-index (defaults to 2000000000)
    className: 'spinner',   // The CSS class to assign to the spinner
    top: '50%',             // Top position relative to parent
    left: '50%',            // Left position relative to parent
    shadow: false,          // Whether to render a shadow
    hwaccel: false,         // Whether to use hardware acceleration
    position: 'absolute'    // Element positioning
  }
  var target = document.getElementById('spinner');
  var spinner = new Spinner(opts);
  var username, organization, password, password_verify,user_type, email;


  $('input#google-sign-in').hover(function() {
  $('input#google-sign-in').attr('src','../static/img/btn_google_signin_dark_focus_web@2x.png');
      }, function() {
  $('input#google-sign-in').attr('src','../static/img/btn_google_signin_dark_normal_web@2x.png');
      });

  // Log in using google.
  $('body').on('click', '#google-sign-in', function(e) {
      $('input#google-sign-in').attr('src','../static/img/btn_google_signin_dark_pressed_web@2x.png');
      e.preventDefault();
  });
  startApp();
  // hide stuff
  $('.spinner-container').hide();
  $('.notification').hide();

  $('#register-form').on('submit', function(e){
    e.preventDefault();

    
    // hide button and show spinner
    $('#submit').hide();
    $('.spinner-container').show();
    spinner.spin(target);

    // validate form with parsley
    var form = $(this);
    form.parsley().validate();
    
    if (form.parsley().isValid()){
      // Get the username and password from registration form.
      username = $('input#username').val();
      organization = $('input#organization').val();
      password = $('input#password').val();
      password_verify = $('input#password1').val();
      user_type = $('input[name=utype]:checked').val();
      email = $('input#email').val();

      if (password === password_verify) {
        $('#terms-modal').modal('show');

      
      } else {
        // hide spinner and show errors
        $('.spinner-container').hide();
        spinner.stop();
        $('#submit').show();
        
        $('#register-form input').removeClass('parsley-success');
        $('#register-form #password').addClass('parsley-error')
        $('#register-form #password1').addClass('parsley-error')
        $('p.notification.notification-success').hide();
        $('p.notification.notification-critical').hide();
        $('p.notification.notification-critical3').hide();
        $('p.notification.notification-critical2').show();
      }
      
      return false;
    }
  });

  $('#modal-form').on('submit', function(e){
     e.preventDefault();

    // validate form with parsley
    var form = $(this);
    form.parsley().validate();
    if (form.parsley().isValid()){
      $('#terms-modal').modal('hide');
      var usertype= "coach";
      var user_data = {
        "username": username,
        "password": password,
        "email": email,
        "user_type": usertype,
        "organization": organization
      };

      $.ajax({
              type: 'POST',
              url: '/api/register/',
              data: JSON.stringify(user_data),
              contentType: 'application/json; charset=utf-8',
              // Registration was successful.
              success: function(data) {
                $('p.notification.notification-critical').hide();
                $('p.notification.notification-critical2').hide();
                $('p.notification.notification-critical3').hide();
                $('p.notification.notification-success').show();
                $('#register-form')[0].reset();
                $.ajax({
                  type: 'POST',
                  dataType: 'json',
                  url: '/api/login/',
                  data: {
                    client_id: 'aHD4NUa4IRjA1OrPD2kJLXyz34c06Bi5eVX8O94p',
                    username: username,
                    password: password,
                    grant_type: 'password'
                  },
                  success: function(data) {
                    // Get the access token and store client side.
                    var access_token = data.access_token;
                    var usertype = data.user.user_type;
                    var username = data.user.username;

                    amplitude.setUserId(username);
                    
                    //Attempting to transition into localStorage.
                    localStorage.setItem('access_token', access_token);
                    localStorage.setItem('usertype', usertype);
                    localStorage.setItem('username', username);
                    
                    location.href = '/home';
                  },
                // Login request failed.
                  error: function(xhr, errmsg, err) {
                    // hide spinner and show error message
                    $('.spinner-container').hide();
                    spinner.stop();
                    $('#submit').show();
                    $('p.notification.notification-critical').show();
                    $('#login-form input')
                        .removeClass('parsley-success')
                        .addClass('parsley-error');
                  }
            });
              },
              // Registration failed.
              error: function(xhr, errmsg, err) {
                // hide spinner, show error
                $('.spinner-container').hide();
                spinner.stop();
                $('#submit').show();

                if(xhr.status==400){
                  var error_message = xhr.responseText;
                  var generic = JSON.parse(error_message)
                  $('#register-form input').removeClass('parsley-success');
                  $('#register-form #username').addClass('parsley-error');
                  $('p.notification.notification-success').hide();
                  $('p.notification.notification-critical').show();
                  $('p.notification.notification-critical2').hide();
                  $('p.notification.notification-critical3').hide();
                  $('p.notification.notification-critical4').hide();
                  if (generic.password)
                    $('p.notification.notification-critical').text('Password Not Valid: '+generic.password);
                  else if (generic.username)
                    $('p.notification.notification-critical').text('Username: '+generic.username);
                  else if (generic.email)
                    $('p.notification.notification-critical').text('Email: '+generic.email);
                }
                else if(xhr.status==500){
                  $('#register-form input').removeClass('parsley-success');
                  $('#register-form').addClass('parsley-error');
                  $('p.notification.notification-success').hide();
                  $('p.notification.notification-critical3').show();
                  $('p.notification.notification-critical2').hide();
                  $('p.notification.notification-critical').hide();

                }
                
              }
            });
        }
    });

  $("body").on('click', '#close-terms' ,function(){
      $('.spinner-container').hide();
      spinner.stop();
      $('#submit').show();
    });


});
