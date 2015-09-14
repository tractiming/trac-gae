if (sessionStorage.access_token == null) {
    //link to login page
    location.href= '/login';
}
else{
	$(document).ready(function() {
		$('li a.logout').click(function(){			
			$.ajax({
				type:"POST",
				url: '/api/logout/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					sessionStorage.clear();
					location.href='/login';
					},
				error: function(xhr, errmsg, err) {
					sessionStorage.clear();
					location.href='/login';
					}	
					
			});
		});
	});
}
