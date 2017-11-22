if (localStorage.usertype == 'athlete'){
	location.href='/home.html';
}

$(function() {
	var idArray = [],
			currentID,
			updateHandler, 
			spinner, target;

	(function init(){

		// initialize spinner
		var opts = {
			lines: 13, 							// The number of lines to draw
		  length: 28, 						// The length of each line
			width: 14, 							// The line thickness
			radius: 42, 						// The radius of the inner circle
			scale: 0.5, 						// Scales overall size of the Spinner
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
		target = document.getElementById('spinner');
		spinner = new Spinner(opts).spin(target);

		// hide all notifications
		$('.notification').hide();

		// get all the readers
		getReaders();
	})();

	//function to load reader info
	function getReaders(){
		$('#results-table').empty();
		$('.notification').hide();

		$.ajax({
			url: '/api/readers/',
			headers: {Authorization: 'Bearer ' + localStorage.access_token},
			dataType: 'text',
			success: function(data) {
				var json = $.parseJSON(data);
				console.log(json);
				if (json == '') {
					$('.notification.no-results').show();
					spinner.stop();
				} else {
					spinner.stop();

					// add table head if empty
					if (!$.trim($('#results-table').html())) {
						$('#results-table').append(
							'<thead>' + 
								'<tr>' +
									'<th style="text-align:center;">Name</th>' +
									'<th style="text-align:center;">ID Number</th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>'
						);
					}

					// now add readers to table
					for (var i=0; i<json.length; i++) {
						$('#results-table tbody').append(
							'<tr id="'+json[i].id+'" data-toggle="modal" data-target="#edit-modal">' +
								'<td>' + json[i].name + '</td>' +
								'<td>' + json[i].id_str + '</td>' +
							'</tr>'
						);
					}

					$('#results-table').show();

					$('#results-table tbody tr').click(function(e) {
						e.preventDefault();
						$('#edit-modal #edit-form input#edit-id').val(this.id);
						$('#edit-modal #edit-form input#edit-name').val($(this).find('td')[0].innerText);
						$('#edit-modal #edit-form input#edit-id-str').val($(this).find('td')[1].innerText);
						$('#edit-modal #edit-form').parsley().reset();
					});
				}
			}
		});
	}

	$('button#add').click(function(e) {
		e.preventDefault();

		$('.notification').hide();

		$('#create-submit').click(function(e) {
			e.preventDefault();
			
			var form = $('#create-form');
			form.parsley().validate();

			if (form.parsley().isValid()) {
				$('#create-modal').modal('hide');
				$('#results-table').hide();
				spinner.spin(target);

				var name = escapeString($('input#create-name').val());
				var idstr = escapeString($('input#create-id-str').val());
				
				form.parsley().reset();
				form[0].reset();

				$.ajax({
					type: 'POST',
					dataType: 'json',
					url: '/api/readers/',
					headers: {Authorization: 'Bearer ' + localStorage.access_token},
					data: {
						name: name,
						id_str: idstr
					},
					success: function(data) {
						spinner.stop();
						getReaders();
						$('.notification-success.register-success').show();
					},
					error: function(xhr, errmsg, err) {
						spinner.stop();
						$('#results-table').show();
						$('.notification-error.server-error').show();
					}
				});
			}
		});

	});

	$('#edit-submit').on('click', function(e) {
		e.preventDefault();

		$('.notification').hide();

		var form = $('#edit-form');
		form.parsley().validate();

		//if the form is valid then submit
		if (form.parsley().isValid()) {
			
			$('#edit-modal').modal('hide');
			$('#results-table').hide();
			spinner.spin(target);

			var id = escapeString($('input#edit-id').val());
			var name = escapeString($('input#edit-name').val());
			var idstr = escapeString($('input#edit-id-str').val());
			$.ajax({
				type: 'PUT',
				dataType:'json',
				url: '/api/readers/'+id,
				headers: {Authorization: 'Bearer ' + localStorage.access_token},
				data: {
					name: name,
					id_str: idstr
				},
				success: function(data) {
					spinner.stop();
					getReaders();
					$('.notification-success.update-success').show();
				},
				error: function(xhr, errmsg, err) {
					spinner.stop();
					$('#results-table').show();
					$('.notification-error.server-error').show();
				}
			});
		}
	});


	$('#delete-submit').on('click', function(e) {
		e.preventDefault();

		$('.notification').hide();
		$('#edit-modal').modal('hide');
		$('#delete-confirm-modal').modal('show');

		var id = $('input#edit-id').val();
		$('#delete-confirm-modal .modal-body button').on('click', function(e) {
			e.preventDefault();
			$('#delete-confirm-modal').modal('hide');
			$('#results-table').hide();
			spinner.spin(target);
			var confirm = $(this).html();
			if (confirm == 'Yes') {
				$.ajax({
					type: 'DELETE',
					dataType: 'json',
					url: '/api/readers/'+id,
					headers: {Authorization: 'Bearer ' + localStorage.access_token},
					success: function(data) {
						spinner.stop();
						getReaders();
						$('.notification-success.delete-success').show();
					},
					error: function(xhr, errmsg, err) {
						spinner.stop();
						$('#results-table').show();
						$('.notification-error.server-error').show();
					}
				});
			} else if (confirm == 'No') {
				$('#delete-confirm-modal').modal('hide');
				$('#edit-modal').modal('show');
			}
		});
	});
});