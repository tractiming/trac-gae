$(function() {
	//prevent form submission on submit, and instead call ajax
	$('#login-form').on('submit', function(e) {
		e.preventDefault();

		//display spinner 
		$('.modal-animate').show();

		//validate that form is filled in--3rd party plugin
		var form = $(this);
		form.parsley().validate();

		//if the form is valid then submit
		if (form.parsley().isValid()) {
			var username = $('input#username').val();
			var password = $('input#password').val();
			
			$.ajax({
				type: "POST",
				dataType:'json',
				url: "/oauth2/access_token/",
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
					sessionStorage.setItem('username',username);
					$.ajax({
						url: "/api/userType/",
						dataType: "text",			//force to handle it as text
						headers: {Authorization: "Bearer " + sessionStorage.access_token},
							success: function(data) {
								//hide spinner
								$(".modal-animate").hide();
								var usertype = data;
								sessionStorage.setItem('usertype',usertype);
								location.href ="/home.html";
							},
							error: function(xhr, errmsg, err) {
								$(".modal-animate").hide();
								$("h6.notification.notification-critical").show();
							}
					});
				},
				// Login request failed.
				error: function(xhr, errmsg, err) {
					//hide spinner then show error message
					$(".modal-animate").hide();
					$("h6.notification.notification-critical").show();
				}
			});
		}
	});
});