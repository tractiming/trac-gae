if (sessionStorage.usertype == 'athlete'){
	location.href = '/home.html';
}

$(function() {
	//===================================== spinner configuration =====================================
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
		position: 'relative'	 	// Element positioning
	}
	var spinner = new Spinner(opts);
	var target;

	//===================================== parsley configuration =====================================
	window.ParsleyConfig = window.ParsleyConfig || {};
	window.ParsleyConfig.validators = window.ParsleyConfig.validators || {};
	window.ParsleyValidator
		.addValidator('date', function(value) {
			var matches = /^(0?[1-9]|1[012])[\/\-](0?[1-9]|[12][0-9]|3[01])[\/\-](\d{4})$/.exec(value.trim());
			if (matches) {
				var m = matches[1],
						d = matches[2],
						y = matches[3];

				date = new Date(y, m-1, d);
				return ((date.getMonth()+1 == m) && (date.getDate() == d) && (date.getFullYear() == y));
			} else 
				return false;
		}, 32).addMessage('en', 'date', 'This value should be a valid date in the form of mm/dd/yyyy.')
		
		.addValidator('time', function(value) {
			return /^(0?[1-9]|1[012])[:]([0-5][0-9])(?:[:]([0-5][0-9]))?$/.test(value.trim());
		}, 32).addMessage('en', 'time', 'This value should be in the form of hh:mm or hh:mm:ss.');

	//=================================== datepicker configuration ====================================
	var datepickerOptions = {
		todayHighlight: true,
		todayBtn: true
	};
	$('input#start-date').datepicker(datepickerOptions);
	$('input#end-date').datepicker(datepickerOptions);

	
	var numSessions = 0,
			sessionFirst = 1,
			sessionLast = 10;
	loadworkouts();

	
	function loadworkouts() {
		$('#results').empty();
		spinner.spin(document.getElementById('spinner-main'));
		$.ajax({
			url: '/api/session_Pag/',
			headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
			data: {
				i1: sessionFirst,
				i2: sessionLast,
			},
			dataType: 'text',
			success: function(data) {
				var json = $.parseJSON(data);
				json = json.reverse();

				if (json == '') {
					$('#results').empty();
					$('button.next').attr('disabled', true);
					$('button.prev').attr('disabled', false);
					$('.notification.no-sessions').show();
				} else {
					// show name and date, dont show message, but show button
					$('.notification.no-sessions').hide();
					$('#results').append(
						'<table id="results-table" class="table table-striped table-hover">' +
							'<thead>' +
								'<tr>' +
									'<th style="display:none;">id</th>' +
									'<th>Workout Name</th>' +
									'<th>Start Date</th>' +
									'<th class="hidden-xs hidden-sm">End Date</th>' +
									'<th class="hidden-xs hidden-sm">Distance</th>' +
									'<th class="hidden-xs hidden-sm">Track</th>' +
									'<th>Filtered</th>' +
									'<th class="hidden-xs hidden-sm">Private</th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>' +
						'</table>'
					);

					for (var i=0; i < json.length; i++) {

						id = json[i].id;
						name = json[i].name;
						distance = json[i].interval_distance;
						track = json[i].track_size;
						filter= json[i].filter_choice;
						privateselect = json[i].private;
						var sTS = UTC2local(json[i].start_time);
						sTS = sTS.substring(0, 25);
						var sTE = UTC2local(json[i].stop_time);
						sTE = sTE.substring(0,25);

						$('#results tbody').append(
							'<tr>'+
								'<td style="display:none;">' + id + '</td>' +
								'<td>'+name+'</td>'+
								'<td>'+sTS+'</td>'+
								'<td class="hidden-xs hidden-sm">'+sTE+'</td>'+
								'<td class="hidden-xs hidden-sm">'+distance+'</td>'+
								'<td class="hidden-xs hidden-sm">'+track+'</td>'+
								'<td>'+filter+'</td>'+
								'<td class="hidden-xs hidden-sm">'+privateselect+'</td>'+
							'</tr>'
						);
					}

					if (json.length < 10) {
						$('button.next').attr('disabled', true);
					} else {
						$('button.next').attr('disabled', false);
					}

					if (sessionFirst == 1){
						$('button.prev').attr('disabled', true);
					} else {
						$('button.prev').attr('disabled', false);
					}
				}
				spinner.stop();
			}
		});
	}

	// creating workout session
	$('body').on('click', 'button#new-session', function(e){
		e.preventDefault();

		// set modal title and reset form
		$('#session-modal .modal-title').html('Create New Workout');
		$('#session-form')[0].reset();
		
		// show corrent buttons
		$('#session-form .session-form-buttons').hide();
		$('#session-form #session-create-buttons').show();

		// bind handler to create button
		$('body').off('click', '#session-create-buttons button#create');
		$('body').on('click', '#session-create-buttons button#create', function(e){
			e.preventDefault();

			//validate that form is correctly filled out
			var form = $('#session-form');
			form.parsley().validate();

			if (form.parsley().isValid()) {
				// reset parsley styling
				form.parsley().reset();

				// hide button and show spinner
				$('#session-form .session-form-buttons').hide();
				target = $('#spinner-form');
				target.css('height', 50);
				spinner.spin(target[0]);

				var title = $('input[id=title]').val();

				// get start date and time
				var startDate = $('input[id=start-date]').val().trim().split(/[\/-]/),
						startTime = $('input[id=start-time]').val().trim().split(':'),
						startAMPM = $('select#start-am-pm').val();
				
				// create start date object
				var startDateTime = new Date();
				startDateTime.setFullYear(startDate[2]);
				startDateTime.setMonth(startDate[0]-1);
				startDateTime.setDate(startDate[1]);

				if ((startAMPM == 'PM' ) && (startTime[0] < 12))
					startDateTime.setHours(startTime[0]+12);
				else if ((startAMPM == 'AM') && (startTime[0] == 12))
					startDateTime.setHours(startTime[0]-12);
				else
					startDateTime.setHours(startTime[0]);

				startDateTime.setMinutes(startTime[1]);

				if (startTime.length > 2)
					startDateTime.setSeconds(startTime[2]);
				else
					startDateTime.setSeconds(0);

				// get end date and time 
				var endDate = $('input[id=end-date]').val().trim().split(/[\/-]/),
						endTime = $('input[id=end-time]').val().trim().split(':'),
						endAMPM = $('select#end-am-pm').val();
				// create end date object
				var endDateTime = new Date();
				endDateTime.setFullYear(endDate[2]);
				endDateTime.setMonth(endDate[0]-1);
				endDateTime.setDate(endDate[1]);

				if ((endAMPM == 'PM' ) && (endTime[0] < 12))
					endDateTime.setHours(endTime[0]+12);
				else if ((endAMPM == 'AM') && (endTime[0] == 12))
					endDateTime.setHours(endTime[0]-12);
				else
					endDateTime.setHours(endTime[0]);

				endDateTime.setMinutes(endTime[1]);
				if (endTime.length > 2)
					endDateTime.setSeconds(endTime[2]);
				else
					endDateTime.setSeconds(0);

				var distance = $('input[id=distance]').val();
				var size = $('input[id=size]').val();
				var filter = $('#filter option:selected').val();
				var privateselect = $('#private option:selected').val();

				$.ajax({
					type: 'POST',
					dataType:'json',
					url: '/api/time_create/',
					headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
					data: {
						id: 0,
						name: title,
						start_time: startDateTime.toISOString(),
						stop_time: endDateTime.toISOString(),
						rest_time: '0',
						track_size: size,
						interval_distance: distance,
						interval_number: '0',
						filter_choice: filter,
						private: privateselect
					},
					success: function(data) {
						// hide spinner
						spinner.stop();
						target.css('height', '');
						
						// show success message
						$('.notification').hide();
						$('.notification.create-success').show();

						// switch modals
						$('#session-modal').modal('hide');
						$('#notifications-modal').modal('show');

						// clear form and reload data
						$('#session-form')[0].reset();
						loadworkouts();
					},
					error: function(xhr, errmsg, err) {
						// hide spinner
						spinner.stop();
						target.css('height', '');
						
						// show error message
						$('.notification').hide();
						$('.notification.form-data-error').show();

						// switch modals
						$('#session-modal').modal('hide');
						$('#notifications-modal').modal('show');
					}
				});
			}
		});
	});

	// editing workout session
	$('body').on('click', '#results-table tr', function(){
		// set modal title and show
		$('#session-modal .modal-title').html('Edit Workout Session');
		$('#session-modal').modal('show');

		// show corrent buttons
		$('#session-form .session-form-buttons').hide();
		$('#session-form #session-edit-buttons').show();

		var data = $(this).children();
		$('input#idnumber').val($(data[0]).html());
		$('input#title').val($(data[1]).html());

		/*
		var value = $(this).html();
		$(value).each(function(index){
			if (index ==0) {
				var input = $('input#idnumber');
				input.val($(this).html() );
			} else if (index ==1) {
				var input =$('input#title');
				input.val($(this).html() );
			} else if (index ==2) {
				var input =$('input#start-date');
				var format = new Date($(this).html());
				format = format.toISOString();
				format = localISOString(format);
				format = format.replace(/T/g,' ');
				format = format.substring(0,19);
				format = format.replace(/;/g, ':');
				input.val(format);
			} else if (index ==3) {
				var input =$('input#end-date');
				var format = new Date($(this).html());
				format = format.toISOString();
				format = localISOString(format);
				format = format.replace(/T/g,' ');
				format = format.substring(0,19);
				format = format.replace(/;/g, ':');
				input.val(format);
			} else if (index ==4) {
				var input =$('input#distance');
				input.val($(this).html() );
			} else if (index ==5) {
				var input =$('input#size');
				input.val($(this).html() );
			} else if (index ==6) {
				var input =$('select#filter');
				input.val($(this).html() );
			} else if (index ==7) {
				var input =$('select#private');
				input.val($(this).html() );
			}
		});
		//*/
	});

	

	$('body').off('click', 'button#delete');
	$('body').on('click', 'button#delete', function(f){
	//alert($(this).html());
		f.preventDefault();
		$('div.notification.notification-warning').show();
		$('div.notification.notification-critical').hide();
		$('div.notification.notification-critical').hide();
		$('div.notification.create-success').hide();
		$('div.notification.update-success').hide();
	});

	$('body').on('click', 'button#warning-yes', function(event){
		var value = $(this).html();
		$('.modal-animate').show();

		var id=$('input[id=idnumber]').val();
		//alert(id);
		//alert(filter);

		$.ajax({
			type: 'DELETE',
			dataType:'json',
			url: '/api/sessions/'+id,
			headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
			success: function(data) {
				//hide spinner, success modal, and reset form
				$('.modal-animate').hide();
				$('div.notification.notification-critical').hide();
				$('div.notification.create-success').hide();
				$('div.notification.update-success').hide();
				$('div.notification.delete-success').show();
				$('div.notification.notification-warning').hide();
				$('#session-form')[0].reset();
				$('button#delete').hide();
				$('input#update').hide();
				$('input#save').show();
				$('p#idnumber').hide();
				//$('input#create').hide();
				$('#results').empty();
				loadworkouts();
			},
			error: function(xhr, errmsg, err) {
				//hide spinner, show error modal
				$('.modal-animate').hide();
				$('div.notification.create-success').hide();
				$('div.notification.notification-warning').hide();
				$('div.notification.update-success').hide();
				$('div.notification.delete-success').hide();
				$('div.notification.notification-critical').show();
			}
		});
	});

	$('button#warning-no').click(function(event){
		$('.modal-animate').hide();
		$('div.notification.create-success').hide();
		$('div.notification.notification-warning').hide();
	});

	$('body').on('hidden.bs.modal', '#notificationModal', function(){
		$('div.notification.delete-success').hide();
		$('div.notification.notification-warning').hide();
	});

	$('body').on('click', 'button.prev', function(f){
		if(sessionFirst != 1){
			sessionFirst -= 10;
			sessionLast -= 10;
		}

		loadworkouts();
	});

	$('body').on('click', 'button.next',function(f){
		sessionFirst += 10;
		sessionLast += 10;
		loadworkouts();
	});

	$('body').on('click', 'input#update',function(f){
		//alert($(this).html());
		f.preventDefault();
		$('.modal-animate').show();
		var id=$('input[id=idnumber]').val();
		var title=$('input[id=title]').val();
		var startDate=$('input[id=start-date]').val();
		var endDate=$('input[id=end-date]').val();
		var distance=$('input[id=distance]').val();
		var size=$('input[id=size]').val();
		var filter=$('#filter option:selected').val();
		var privateselect=$('#private option:selected').val();
		var sT = local2UTC(startDate);
		var eT = local2UTC(endDate);

		$.ajax({
			type: 'POST',
			dataType:'json',
			url: '/api/time_create/',
			headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
			data: {
				id: id,
				name: title,
				start_time: sT,
				stop_time: eT,
				rest_time: '0',
				track_size: size,
				interval_distance: distance,
				interval_number:'0',
				filter_choice:filter,
				private:privateselect,
			},
			success: function(data) {
				//hide spinner, success modal, and reset form
				$('.modal-animate').hide();
				$('div.notification.notification-critical').hide();
				$('div.notification.create-success').hide();
				$('div.notification.delete-success').hide();
				$('div.notification.update-success').show();
				$('#session-form')[0].reset();
				$('button#delete').hide();
				$('input#update').hide();
				$('input#save').show();
				$('p#idnumber').hide();
				//$('input#create').hide();
				loadworkouts();
			},
			error: function(xhr, errmsg, err) {
				//hide spinner, show error modal
				$('.modal-animate').hide();
				$('div.notification.create-success').hide();
				$('div.notification.notification-warning').hide();
				$('div.notification.update-success').hide();
				$('div.notification.delete-success').hide();
				$('div.notification.notification-critical').show();
			}
		});
	});
});