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

	//===================================== create.js functions =======================================
	var SESSIONS_PER_PAGE = 10,
			FORM_CREATE = 0, CSV_CREATE = 1;

	var numSessions = 0,
			currentPage = 1,
			sessionFirst = 1,
			sessionLast = SESSIONS_PER_PAGE;
	loadWorkouts();

	
	function loadWorkouts() {
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

				var results = json.results
				numSessions = json.num_sessions;

				if (numSessions == 0) {
					$('#results').empty();
					$('button.next').attr('disabled', true);
					$('button.prev').attr('disabled', true);
					$('.notification.no-sessions').show();
					$('.sessions-navigate').hide();
				} else {
					// show name and date, dont show message, but show button
					$('.notification.no-sessions').hide();
					$('.sessions-navigate').show();

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

					for (var i=0; i < results.length; i++) {

						id = results[i].id;
						name = results[i].name;
						distance = results[i].interval_distance;
						track = results[i].track_size;
						filter= results[i].filter_choice == true ? 'Yes' : 'No';
						privateselect = results[i].private == true ? 'Yes' : 'No';
						var sTS = UTC2local(results[i].start_time);
						sTS = sTS.substring(0, 25);
						var sTE = UTC2local(results[i].stop_time);
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

					if (numSessions < SESSIONS_PER_PAGE) {
						$('button.prev').attr('disabled', true);
						$('button.next').attr('disabled', true);
					} else {
						if ((results.length < SESSIONS_PER_PAGE) || (sessionLast == numSessions))
							$('button.next').attr('disabled', true);
						else
							$('button.next').attr('disabled', false);

						if (sessionFirst == 1)
							$('button.prev').attr('disabled', true);
						else
							$('button.prev').attr('disabled', false);
					}

					// add page number and status
					$('.sessions-page-number').html(currentPage);
					$('.sessions-show-status').html(
						'Showing '+
							sessionFirst+' - '+ 
							(sessionLast > numSessions ? numSessions : sessionLast) +' of '+
							numSessions+' results');
				}
				spinner.stop();
			}
		});
	}

	// creating workout session
	$('body').on('click', 'button#new-session', function(e){
		e.preventDefault();

		var createType;
		if ($('#create-type-nav').find('.active').attr('id') === 'create-with-form')
			createType = FORM_CREATE;
		else
			createType = CSV_CREATE;

		// set modal title
		$('#form-modal .modal-title').html('Create New Workout');
		$('#create-type-nav').show();

		// reset forms
		$('#session-form')[0].reset();
		$('#csv-form')[0].reset();

		// show correct form
		if ($('#create-type-nav').find('.active').attr('id') === 'create-with-form') {
			$('#csv-form').hide();
			$('#session-form').show();
		} else {
			$('#session-form').hide();
			$('#csv-form').show();
		}
		
		// show corrent buttons
		$('.session-form-buttons').hide();
		$('#session-create-buttons').show();

		// register handler to upload type selection
		$('body').off('click', 'ul#create-type-nav li');
		$('body').on('click', 'ul#create-type-nav li', function(e) {
			e.preventDefault();
			$(this).parent().children().removeClass('active');
			$(this).addClass('active');

			if ($(this).attr('id') === 'create-with-form') {
				$('#csv-form').hide();
				$('#session-form').show();
				createType = FORM_CREATE;
			} else {
				$('#session-form').hide();
				$('#csv-form').show();
				createType = CSV_CREATE;
			}
		});

		// add feedback on file selection
		$('.btn-file :file').off('fileselect');
		$('.btn-file :file').on('fileselect', function(e, numFiles, label) {
			var input = $(this).parents('.input-group').find(':text'),
					log = numFiles > 1 ? numFiles + ' files selected' : label;

			if( input.length ) {
				input.val(log);
			} else {
				if( log ) alert(log);
			}
		});

		// trigger event on file selection
		$('body').off('change', '.btn-file :file');
		$('body').on('change', '.btn-file :file', function() {
			var input = $(this),
					numFiles = input.get(0).files ? input.get(0).files.length : 1,
					label = input.val().replace(/\\/g, '/').replace(/.*\//, '');

			input.trigger('fileselect', [numFiles, label]);
		});

		// register handler to create button
		$('body').off('click', '#session-create-buttons button#create');
		$('body').on('click', '#session-create-buttons button#create', function(e){
			e.preventDefault();

			if (createType === FORM_CREATE) {
				//validate that form is correctly filled out
				var form = $('#session-form');
				form.parsley().validate();

				if (!form.parsley().isValid())
					return;

				// reset parsley styling
				form.parsley().reset();

				// hide button and show spinner
				$('.session-form-buttons').hide();
				target = $('#spinner-form');
				target.css('height', 50);
				spinner.spin(target[0]);

				var title = escapeString($('input[id=title]').val());

				// get start date and time
				var startDate = $('input[id=start-date]').val().trim().split(/[\/-]/),
						startTime = $('input[id=start-time]').val().trim().split(':').map(Number),
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
						endTime = $('input[id=end-time]').val().trim().split(':').map(Number),
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
				var filter = $('input[name=filter]:checked').val() == 'yes';
				var privateselect = $('input[name=private]:checked').val() == 'yes';

				//*
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
						$('#form-modal').modal('hide');
						$('#notifications-modal').modal('show');

						// clear form and reload data
						$('#session-form')[0].reset();
						loadWorkouts();
					},
					error: function(xhr, errmsg, err) {
						// hide spinner
						spinner.stop();
						target.css('height', '');
						
						// show error message
						$('.notification').hide();
						$('.notification.server-error').show();

						// switch modals
						$('#form-modal').modal('hide');
						$('#notifications-modal').modal('show');
					}
				});
			} else if (createType === CSV_CREATE) {

				var data;
				$('#csv-form input[type=file]').parse({
					config: {
						delimiter: '',								// auto-detect
						newline: '',									// auto-detect
						header: false,								// no column names
						dynamicTyping: false,					// convert numbers into numbers and booleans to booleans
						preview: 0,										// parse all rows if 0, or specify number of rows
						encoding: '',									// auto-detect
						worker: true,									// run on separate thread--slower but won't lock webpage
						comments: false,							// no comments in file
						step: stepFn,									// callback executed after every row
						complete: completeFn,					// callback for when parsing is complete
						error: undefined,							// callback for when FileReader encounters an error
						download: false,							// true for URL download, false otherwise
						skipEmptyLines: true,					// skip empty lines
						chunk: undefined,							// callback executed after every chunk
						fastMode: undefined,					// speed up parsing for input without quoted fields
						beforeFirstChunk: undefined,	// function to execute before parsing first chunk
					},
					before: function(file, inputElem) {
						// executed before parsing each file begins;
						// what you return here controls the flow

						// hide button and show spinner
						$('.session-form-buttons').hide();
						target = $('#spinner-form');
						target.css('height', 50);
						spinner.spin(target[0]);

						// initialize array of parsed data
						data = [];
					},
					error: function(err, file, inputElem, reason) {
						// executed if an error occurs while loading the file,
						// or if before callback aborted for some reason
						console.log(err);
					},
					complete: function() {
						// executed after all files are complete
						console.log('Finished parsing all files.');
					}
				});

				function stepFn(results, parser) {
					//console.log('Row data:', results.data);
					//console.log('Row errors:', results.errors);
					var row = results.data[0];
					for (var i=0; i<row.length; i++) {
						if (row[i] != '') {
							data.push(row);
							break;
						}
					}
				}

				function completeFn(results, file) {
					// executed after each file is complete
					console.log('Finished parsing '+file.name, file);
					
					var title = data[0][1].trim(),
							date = data[1][1],
							time = data[2][1],
							trackSize = Number(data[3][1]),
							intervalDistance = Number(data[4][1]),
							workoutResults = data.slice(6);

					// format time to ISO string
					var start_time = new Date(date+' '+time).toISOString();

					// format results
					results = [];
					for(var i=0; i<workoutResults.length; i++) {
						runner = workoutResults[i];
						
						// set corresponding fields in dictionary
						temp = {};
						temp.username = runner[0].trim();
						temp.last_name = runner[1].trim();
						temp.first_name = runner[2].trim();
						temp.splits = runner.slice(3);

						for(var j=0; j<temp.splits.length; j++) {
							var split = temp.splits[j];

							if (split == '') {
								temp.splits.splice(j);
								break;
							}

							if (split.indexOf(':') === -1) {
								var s = split.split('.');

								var remainder = Number(s[0])%60;
								var secs = remainder < 10 ? '0'+remainder.toString() : remainder.toString();

								temp.splits[j] = (Math.floor(Number(s[0])/60)).toString() +':'+ secs +'.'+ (s[1] ? s[1] : '000');
							} else if (split.indexOf('.') === -1) {
								temp.splits[j] = split + '.000';
							}
						}

						// add to results
						results.push(temp);
					}

					// construct json to send to server
					var json = {
						'title': title,
						'start_time': start_time,
						'track_size': trackSize,
						'interval_distance': intervalDistance,
						'results': results
					};

					$.ajax({
						type: 'POST',
						dataType: 'json',
						url: '/api/upload_workouts/',
						headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
						data: JSON.stringify(json),
						success: function(data) {
							// hide spinner
							spinner.stop();
							target.css('height', '');
							
							// show success message
							$('.notification').hide();
							$('.notification.create-success').show();

							// switch modals
							$('#form-modal').modal('hide');
							$('#notifications-modal').modal('show');

							// clear form and reload data
							$('#session-form')[0].reset();
							loadWorkouts();
						},
						error: function(xhr, errmsg, err) {
							// hide spinner
							spinner.stop();
							target.css('height', '');
							
							// show error message
							$('.notification').hide();
							$('.notification.server-error').show();

							// switch modals
							$('#form-modal').modal('hide');
							$('#notifications-modal').modal('show');
						}
					});
				}
			}
		});
	});

	// editing workout session
	$('body').on('click', '#results-table tbody tr', function(){
		// set modal title and show
		$('#form-modal .modal-title').html('Edit Workout Session');
		$('#create-type-nav').hide();
		$('#csv-form').hide();
		$('#session-form').show();
		$('#form-modal').modal('show');

		// clear form
		$('#session-form').parsley().reset();
		//$('#session-form')[0].reset();

		// populate form with current data
		var data = $(this).children();
		$('input#idnumber').val($(data[0]).html());
		$('input#title').val($(data[1]).html());

		var startDate = new Date($(data[2]).html());
		$('input#start-date').datepicker('update', startDate);

		var startTime = startDate.toTimeString().substring(0,8);
		var startHours = startDate.getHours();
		if (startHours < 12) {
			$('select#start-am-pm').val('AM');
			if (startHours == 0)
				startTime = '12' + startTime.substring(2);
			else if (startHours < 10)
				startTime = startTime.substring(1);
		} else {
			$('select#start-am-pm').val('PM');
			if (startHours > 12)
				startTime = (startHours-12) + startTime.substring(2);
		}
		$('input#start-time').val(startTime);

		var endDate = new Date($(data[3]).html());
		$('input#end-date').datepicker('update', endDate);

		var endTime = endDate.toTimeString().substring(0,8);
		var endHours = endDate.getHours();
		if (endHours < 12) {
			$('select#end-am-pm').val('AM');
			if (endHours == 0)
				endTime = '12' + endTime.substring(2);
			else if (endHours < 10)
				endTime = endTime.substring(1);
		} else {
			$('select#end-am-pm').val('PM');
			if (endHours > 12)
				endTime = (endHours-12) + endTime.substring(2);
		}
		$('input#end-time').val(endTime);

		$('input#distance').val($(data[4]).html());
		$('input#size').val($(data[5]).html());

		if ($(data[6]).html() === 'Yes')
			$('input#filter-yes').prop('checked', true);
		else
			$('input#filter-no').prop('checked', true);

		if ($(data[7]).html() === 'Yes')
			$('input#private-yes').prop('checked', true);
		else
			$('input#private-no').prop('checked', true);

		// show corrent buttons
		$('.session-form-buttons').hide();
		$('#session-edit-buttons').show();

		// bind handler to update button
		$('body').off('click', 'button#update');
		$('body').on('click', 'button#update', function(e) {
			e.preventDefault();

			//validate that form is correctly filled out
			var form = $('#session-form');
			form.parsley().validate();

			if (!form.parsley().isValid())
				return;

			// reset parsley styling
			form.parsley().reset();

			// hide button and show spinner
			$('.session-form-buttons').hide();
			target = $('#spinner-form');
			target.css('height', 50);
			spinner.spin(target[0]);

			var id = $('input[id=idnumber]').val();
			var title = escapeString($('input[id=title]').val());

			// get start date and time
			var startDate = $('input[id=start-date]').val().trim().split(/[\/-]/),
					startTime = $('input[id=start-time]').val().trim().split(':').map(Number),
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
					endTime = $('input[id=end-time]').val().trim().split(':').map(Number),
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
			var filter = $('input[name=filter]:checked').val() == 'yes';
			var privateselect = $('input[name=private]:checked').val() == 'yes';

			//*
			$.ajax({
				type: 'POST',
				dataType:'json',
				url: '/api/time_create/',
				headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
				data: {
					id: id,
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
					$('.notification.update-success').show();

					// switch modals
					$('#form-modal').modal('hide');
					$('#notifications-modal').modal('show');

					// clear form and reload data
					$('#session-form')[0].reset();
					loadWorkouts();
				},
				error: function(xhr, errmsg, err) {
					// hide spinner
					spinner.stop();
					target.css('height', '');
					
					// show error message
					$('.notification').hide();
					$('.notification.server-error').show();

					// switch modals
					$('#form-modal').modal('hide');
					$('#notifications-modal').modal('show');
				}
			});
			//*/
		});

		$('body').off('click', 'button#delete');
		$('body').on('click', 'button#delete', function(e) {
			e.preventDefault();

			// ask for confirmation
			$('.session-form-buttons').hide();
			$('#session-delete-buttons').show();

			$('body').off('click', 'button#delete-yes');
			$('body').on('click', 'button#delete-yes', function(e){
				e.preventDefault();

				// hide buttons and show spinner
				$('.session-form-buttons').hide();
				target = $('#spinner-form');
				target.css('height', 50);
				spinner.spin(target[0]);

				var id = $('input[id=idnumber]').val();

				$.ajax({
					type: 'DELETE',
					dataType:'json',
					url: '/api/sessions/'+id,
					headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
					success: function(data) {
						// hide spinner
						spinner.stop();
						target.css('height', '');
						
						// show success message
						$('.notification').hide();
						$('.notification.delete-success').show();

						// switch modals
						$('#form-modal').modal('hide');
						$('#notifications-modal').modal('show');

						// clear form and reload data
						$('#session-form')[0].reset();
						loadWorkouts();
					},
					error: function(xhr, errmsg, err) {
						// hide spinner
						spinner.stop();
						target.css('height', '');
						
						// show error message
						$('.notification').hide();
						$('.notification.server-error').show();

						// switch modals
						$('#form-modal').modal('hide');
						$('#notifications-modal').modal('show');
					}
				});
			});

			$('body').off('click', 'button#delete-no');
			$('body').on('click', 'button#delete-no', function(e){
				e.preventDefault();

				// show edit buttons
				$('.session-form-buttons').hide();
				$('#session-edit-buttons').show();
			});
		});
	});

	$('body').on('click', 'button.prev', function(e){
		e.preventDefault();

		if (sessionFirst != 1) {
			sessionFirst -= SESSIONS_PER_PAGE;
			sessionLast -= SESSIONS_PER_PAGE;
			currentPage--;
		}

		loadWorkouts();
	});

	$('body').on('click', 'button.next', function(e){
		e.preventDefault();

		sessionFirst += SESSIONS_PER_PAGE;
		sessionLast += SESSIONS_PER_PAGE;
		currentPage++;

		loadWorkouts();
	});
});
