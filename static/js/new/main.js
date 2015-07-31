/* All shared functions */

// jQuery ajax error handling
$(function() {
	$.ajaxSetup({
		error: function(jqXHR, exception) {
			if (jqXHR.status === 0) {
				console.log('Not connected.\n Verify network.');
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

// checks for idle pages and responds according to user response
function idleCheck(handler, resetFunction, resetInterval, resetTimeout, redirectURL){
	clearInterval(handler);
	$('#idle-overlay').show();
	$('#idle-yes').click(function(){
		$('#idle-overlay').hide();
		handler = setInterval(resetFunction, resetInterval);
		setTimeout(function(){ idleCheck(handler, resetFunction, resetInterval, redirectURL); }, resetTimeout);
	});
	$('#idle-no').click(function(){
		$('#idle-overlay').hide();
		window.location.assign(redirectURL);
	});
}

function escapeString(string){
	var specialChars = { 
		"&": "&amp;",
		"<": "&lt;",
		">": "&gt;",
		'"': '&quot;',
		"'": '&#39;',
		"/": '&#x2F;'
	};
	string = String(string).replace(/[&<>"'\/]/g, function(s){
		return specialChars[s];
	});
	
	return string;
}

// force numbers on keypress; input is a jQuery object(s)
// use this function only when DOM is fully loaded
function forceNumeric(input) {
	input.keypress(function(e) {
		return /\d|\./.test(String.fromCharCode(e.keyCode));
	});
}