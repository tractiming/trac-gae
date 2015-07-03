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
      var username = $('input#username').val();
      var organization = $('input#organization').val();
      var password = $('input#password').val();
      var password_verify = $('input#password1').val();
      var user_type = $('input[name=utype]:checked').val();

      if (password === password_verify) {
        $.ajax({
          type: 'POST',
          url: '/api/register/',
          data: {
            username: username,
            password: password,
            organization: organization,
            user_type: user_type
          },
          // Registration was successful.
          success: function(data) {
            $('p.notification.notification-critical').hide();
            $('p.notification.notification-critical2').hide();
            $('p.notification.notification-success').show();
            $('#register-form')[0].reset();
            window.location.href = '/home';
          },
          // Registration failed.
          error: function(xhr, errmsg, err) {
            // hide spinner, show error
            $('.spinner-container').hide();
            spinner.stop();
            $('#submit').show();

            $('#register-form input').removeClass('parsley-success');
            $('#register-form #username').addClass('parsley-error');
            $('p.notification.notification-success').hide();
            $('p.notification.notification-critical').show();
            $('p.notification.notification-critical2').hide();
          }
        });
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
        $('p.notification.notification-critical2').show();
      }
      
      return false;
    }
  });
});