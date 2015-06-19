$(function() {

	// initialize spinner
	var opts = {
		lines: 13, 							// The number of lines to draw
	  length: 28, 						// The length of each line
		width: 14, 							// The line thickness
		radius: 42, 						// The radius of the inner circle
		scale: 0.3, 						// Scales overall size of the Spinner
		corners: 1, 						// Corner roundness (0..1)
		color: '#3577a8', 			// #rgb or #rrggbb or array of colors
		opacity: 0.25, 					// Opacity of the lines
		rotate: 0, 							// The rotation offset
		direction: 1, 					// 1: clockwise, -1: counterclockwise
		speed: 1, 							// Rounds per second
		trail: 60, 							// Afterglow percentage
		fps: 20, 								// Frames per second when using setTimeout() as a fallback for CSS
		zIndex: 1,	 						// The z-index (defaults to 2000000000)
		className: 'spinner', 	// The CSS class to assign to the spinner
		top: '50%', 						// Top position relative to parent
		left: '50%', 						// Left position relative to parent
		shadow: false, 					// Whether to render a shadow
		hwaccel: false, 				// Whether to use hardware acceleration
		position: 'absolute'	 	// Element positioning
	}
	var target = document.getElementById('spinner');
	var spinner = new Spinner(opts);

	// hide stuff
	$('.spinner-container').hide();
	$('p.notification.notification-critical').hide();

	// submit form
	$('#login-form').on('submit', function(e) {
		e.preventDefault();

		// hide button and show spinner
		$('#submit').hide();
		$('.spinner-container').show();
		spinner.spin(target);

		// validate form with parsley
		var form = $(this);
		form.parsley().validate();

		//if the form is valid then submit
		if (form.parsley().isValid()) {
			var username = $('input#username').val();
			var password = $('input#password').val();
			
			$.ajax({
				type: 'POST',
				dataType:'json',
				url: '/oauth2/access_token/',
				data: {
					username: username,
					password: password,
					grant_type: 'password',
					client_id: username
				},
				// Login was successful.
				success: function(data) {
					// Get the access token and store client side.
					var access_token = data.access_token;
					sessionStorage.setItem('access_token', access_token);
					sessionStorage.setItem('username', username);
					$.ajax({
						url: '/api/userType/',
						dataType: 'text',			//force to handle it as text
						headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
							success: function(data) {
								var usertype = data;
								sessionStorage.setItem('usertype', usertype);
								location.href = '/home';
							},
							error: function(xhr, errmsg, err) {
								$('.spinner-container').hide();
								spinner.stop();
								$('#submit').show();
								$('p.notification.notification-critical').show();
								$('#login-form input').removeClass('parsley-success').addClass('parsley-error');
							}
					});
				},
				// Login request failed.
				error: function(xhr, errmsg, err) {
					// hide spinner and show error message
					$('.spinner-container').hide();
					spinner.stop();
					$('#submit').show();
					$('p.notification.notification-critical').show();
					$('#login-form input').removeClass('parsley-success').addClass('parsley-error');
				}
			});
		}
	});
});