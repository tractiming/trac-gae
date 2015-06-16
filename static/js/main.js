/* All shared functions */

// jQuery ajax error handling
$(function() {
	$.ajaxSetup({
		error: function(jqXHR, exception) {
			if (jqXHR.status === 0) {
				console.log('Not connect.\n Verify Network.');
			} else if (jqXHR.status == 404) {
				console.log('Requested page not found. [404]');
			} else if (jqXHR.status == 500) {
				console.log('Internal Server Error [500].');
			} else if (exception === 'parsererror') {
				console.log('Requested JSON parse failed.');
			} else if (exception === 'timeout') {
				console.log('Time out error.');
			} else if (exception === 'abort') {
				console.log('Ajax request aborted.');
			} else {
				console.log('Uncaught Error.\n' + jqXHR.responseText);
			}
		}
	});
});