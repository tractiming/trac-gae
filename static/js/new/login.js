$(function() {

	$('p.notification.notification-critical').hide();

	// submit form
	$('#login-form').on('submit', function(e) {
		e.preventDefault();

		//validate that form is filled in--3rd party plugin
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
								location.href = '/home.html';
							},
							error: function(xhr, errmsg, err) {
								$('p.notification.notification-critical').show();
								$('#login-form input').removeClass('parsley-success').addClass('parsley-error');
							}
					});
				},
				// Login request failed.
				error: function(xhr, errmsg, err) {
					// show error message
					$('p.notification.notification-critical').show();
					$('#login-form input').removeClass('parsley-success').addClass('parsley-error');
				}
			});
		}
	});
});