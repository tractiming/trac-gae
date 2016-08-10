if (localStorage.access_token == null) {
    //link to login page
    location.href= '/login';
}
else{
	console.log('hit else');
	$.ajax({
	  type: 'GET',
	  url: '/api/verifyLogin/',
	  data: {
	  	token: localStorage.access_token
	  },
	  dataType:'json',

	  // Registration was successful.
	  success: function(data) {
	  },
	  // Registration failed.
	  error: function(xhr, errmsg, err) {
	  	sessionStorage.clear();
	  	localStorage.clear();
	  	location.href='/login';
	  },
	  });
}

	$(document).ready(function() {
		$('li a.logout').click(function(){	
					sessionStorage.clear();
					localStorage.clear();
					amplitude.setUserId(null);
					location.href='/login';		
			//$.ajax({
				//type:"POST",
				//url: '/api/logout/',
				//headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				//dataType: 'text',
				//success: function(data) {
					//sessionStorage.clear();
					//location.href='/login';
					//},
				//error: function(xhr, errmsg, err) {
					//sessionStorage.clear();
					//location.href='/login';
					//}	
					
			//});
		});
	});

