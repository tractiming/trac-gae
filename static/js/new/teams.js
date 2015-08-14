$(function() {
	var spinner, target;

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
			position: 'relative'	 	// Element positioning
		}
		target = document.getElementById('spinner');
		spinner = new Spinner(opts).spin(target);

		// hide all notifications
		$('.notification').hide();

		// get all teams/organizations
		getTeams();
	})();

	function getTeams() {
		$.ajax({
			url: '/api/teams/',
			data: { public: true },
			dataType: 'text',
			success: function(data){
				var data = $.parseJSON(data);
				if (data.length == 0){ 
					spinner.stop();
					$('#results-table').hide();
					$('p.notification.notification-default').show();
				} else {
					$('#results-table').append(
						'<thead>' +
							'<tr>' +
								'<th style="text-align:center;">Team Name</th>' +
							'</tr>' +
						'</thead>' +
						'<tbody>' +
						'</tbody>');

					// sort all teams
					var teams = [];
					for (var i=0; i<data.length; i++){
						teams.push(data[i].name);
					}
					teams.sort();

					// now add to team select dropdown
					for (var i=0; i < teams.length; i++){
						$('#results-table tbody').append(
							'<tr id="'+teams[i]+'" onclick="document.location = \'/score/'+teams[i]+'\';" style="cursor:pointer;">' + 
								'<td>'+teams[i]+'</td>' +
							'</tr>');
					}

					$('#results-table').tablesorter();
					var $rows = $('#results-table > tbody > tr');
					$('#search').keyup(function() {
						var val = $.trim($(this).val()).replace(/ +/g, ' ').toLowerCase();

						$rows.show().filter(function() {
							var text = $(this).text().replace(/\s+/g, ' ').toLowerCase();
							return !~text.indexOf(val);
						}).hide();
					});

					spinner.stop();
					$('#results-table').show();
					$('.notification').hide();
				}
			}
		});
	}
});