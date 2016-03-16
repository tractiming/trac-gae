// setup Google charts api
google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function() {

		//===================================== CONSTANTS & variables =====================================
		var TABLE_VIEW = 0,
				GRAPH_VIEW = 1,
				IND_FINAL_VIEW = 2,
				TEAM_FINAL_VIEW = 3;

		var UPDATE_INTERVAL = 5000,				// update live results every 5 secs
				IDLE_TIMEOUT = 1200000;				// idle check after 20 minutes

		var RESULTS_PER_PAGE = 25;				// number of results per page

		var idArray = [],
				currentID=380, currentView,												// used to identify current session and view
				updateHandler, idleHandler,										// interval handlers
				ajaxRequest, correctionAjaxRequest,						// used to keep track of ajax requests
				sessionData, sessionResults,									// current session data
				resultOffset = 0, currentPage = 1,						// for results pagination
				correctionData,	numCorrections,								// auto correction data
				spinner, opts, target, 												// spinner variables
				//teamSpinners = {},			// team spinners
				currentTeamID, currentTeam,										// used in team results tab
				calendarEvents,																// holds list of sessions formatted for fullcalendar
				sessionFirst = 1, sessionLast = 15,						// used for sessions pagination
				cStart, cStop,																// used for date-based sessions query
				switchery, switcheryTarget;										// used for switchery iOS 7 style checkbox slider

		//===================================== spinner configuration =====================================
		opts = {
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
		spinner = new Spinner(opts);

		//====================================== page initialization ======================================
		// default view to table
		currentView = TABLE_VIEW;

		// hide notifications and results
		$('.notification').hide();
		$('#results-nav').hide();
		$('.results-tab-content').hide();
		$('#download-container').hide();
		$('#results-title').html('Results: ' + 'Badwater Cape Fear');


		// query for all workout sessions
		$('#spinner').css('height', 150);
		spinner.spin(target);
		findScores();
		loadCalendar();

		// start updates
		startUpdates();

		//====================================== live_view functions ======================================
		function startUpdates() {
			// stop execution if session is over
			if (sessionData && (new Date() > new Date(sessionData.stop_time)))
				return;

			// refresh the view every 5 seconds to update
			updateHandler = setInterval(lastSelected, UPDATE_INTERVAL);

			// idle check after 20 minutes
			idleHandler = setTimeout(function(){ idleCheck(updateHandler, lastSelected, UPDATE_INTERVAL, IDLE_TIMEOUT, 'http://www.trac-us.com'); }, IDLE_TIMEOUT);
		}

		function stopUpdates() {
			clearInterval(updateHandler);
			clearTimeout(idleHandler);
		}

		function lastSelected(){
			update(currentID, currentView);
		}

		function update(idjson, view) {			
			
			// abort current update and start new ajax request
			if (ajaxRequest)
				ajaxRequest.abort();

			if (view === TABLE_VIEW)
				data = {'limit': resultOffset + RESULTS_PER_PAGE, 'offset': resultOffset};
			else if (view === GRAPH_VIEW)
				data = {};
			else if (view === IND_FINAL_VIEW) {
				$('#results-table #table-canvas').empty();
				$('#results-graph #graph-canvas').empty();
				$('#results-graph #graph-toggle-options').empty();
				$('#results-individual').show();
				spinner.stop();
				$('#spinner').css('height', '');
				$('.notification').hide();
				$('#results-nav').show();
				drawIndividual();
				return;
			} else if (view === TEAM_FINAL_VIEW) {
				$('#results-table #table-canvas').empty();
				$('#results-graph #graph-canvas').empty();
				$('#results-graph #graph-toggle-options').empty();
				spinner.stop();
				$('#spinner').css('height', '');
				$('.notification').hide();
				$('#results-nav').show();
				drawTeam();
				return;
			}
			//if workoutid is undefined, break loop, prevent ajax call
			if (idjson == undefined || idjson === null)
				return;
			ajaxRequest = $.ajax({
				url: '/api/sessions/'+ idjson + '/individual_results',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				data: data,
				dataType: 'text',
				success: function(data) {
					data = $.parseJSON(data);

					var results = data.results;

					// if empty, hide spinner and show notification
					if (results.length === 0) {
						spinner.stop();
						$('#spinner').css('height', '');
						$('.notification.no-data').show();
						$('#download-container').hide();
						$('#results-nav').hide();
						$('.results-navigate-container').hide();
						$('.results-tab-content').hide();
						$('#results-table #table-canvas').empty();
						$('#results-graph #graph-canvas').empty();
						$('#results-graph #graph-toggle-options').empty();
					} else {
						spinner.stop();
						$('#spinner').css('height', '');
						$('.notification').hide();
						$('#results-nav').show();
						$('.results-navigate-container').show();

						// hide all tab contents
						$('.results-tab-content').hide();

						if (view === TABLE_VIEW) {
							$('#results-graph #graph-canvas').empty();
							$('#results-graph #graph-toggle-options').empty();
							drawTable(data);
						} else if (view === GRAPH_VIEW) {
							$('#results-table #table-canvas').empty();
							drawGraph(data);
						}
					}
				}
			});
		}

		//==================================== TABLE VIEW ====================================

		function drawTable(data){
			var results = data.results;
			//*
			// add table skeleton if empty
			if (!$.trim($('#table-canvas').html())) {
				$('#table-canvas').append(
					'<thead>' + 
						'<tr>' +
							'<th>Place</th>' +
							'<th>Name</th>' +
							'<th>Latest Split</th>' +
							'<th>Total Time</th>' +
							'<th class="hidden-xs" style="width:50px;"></th>' +
						'</tr>' +
					'</thead>' +
					'<tbody id="">' +
					'</tbody>'
				);
			}

			for (var i=0; i < results.length; i++) {
				var runner = results[i];

				var id = runner.id,
						place = i + 1 + resultOffset;
						name = runner.name,
						splits = runner.splits,
						total = Number(runner.total);

				// check if row exists
				var row = $('#table-canvas>tbody>tr#results-'+id);
				if (row.length === 1) {
					var numDisplayedSplits = $('table#splits-'+id+'>tbody>tr').length;
					// update splits table
					if (splits.length > numDisplayedSplits) {
						//var totalTime = $('#total-time-'+id).html().split(':');
						//var total = Number(totalTime[0])*60 + Number(totalTime[1]);
						
						// add the new splits if not already displayed
						for (var j=numDisplayedSplits; j<splits.length; j++) {
							var split = Number(splits[j][0]).toFixed(3);
							$('table#splits-'+id+'>tbody').append(
								'<tr>' + 
									'<td class="split-number">' + (j+1) + '</td>' + 
									'<td class="split-time">' + split + '</td>' + 
									'<td class="split-edit-options hidden-xs">' +
										
									'</td>' + 
								'</tr>'
							);
							//total += Number(split);
						}

						// then update latest split and total time
						$('#place-'+id).html(place);
						$('#latest-split-'+id).html(splits[splits.length-1][0]);
						$('#total-time-'+id).html(formatTime(total));
					}
				} else {
					addNewRow(id, name, splits, total, place);
				}
			}

			var numResults = data.num_results;
			var numReturned = data.num_returned;

			if (numResults < RESULTS_PER_PAGE) {
				$('button.prev').attr('disabled', true);
				$('button.next').attr('disabled', true);
			} else {
				if ((numReturned < RESULTS_PER_PAGE) || (numReturned * currentPage == numResults))
					$('button.next').attr('disabled', true);
				else
					$('button.next').attr('disabled', false);

				if (currentPage == 1)
					$('button.prev').attr('disabled', true);
				else
					$('button.prev').attr('disabled', false);
			}

			// add page number and status
			$('.results-page-number').html(currentPage);
			$('.results-show-status').html(
				'Showing '+
					(resultOffset+1) +' - '+ 
					(resultOffset+numReturned) +' of '+
					numResults+' results'
			);

			// show results
			$('#results-table').show();
			$('#download-container').show();
		}

		function addNewRow(id, name, splits, total, place){
			var split = 0;
			if (splits.length > 0)
				latestSplit = splits[splits.length-1][0];
			else
				latestSplit = 'NT';

			$('#table-canvas>tbody').append(
				'<tr id="results-'+id+'" class="accordion-toggle" data-toggle="collapse" data-parent="#table-canvas" data-target="#collapse-'+id+'" aria-expanded="false" aria-controls="collapse-'+id+'">' + 
					'<td id="place-+'+id+'"">' + place + '</td>'+
					'<td>' + name + '</td>' +
					'<td id="latest-split-'+id+'">' + latestSplit + '</td>' + 
					'<td id="total-time-'+id+'"></td>' + 
					'<td id="modify-total-time-'+id+'" class="hidden-xs" style="width:50px;">' +
						'<div class="modify-total-time pull-right" style="display:none;">' +
							'<div class="edit-total"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
						'</div>' +
					'</td>' +
				'</tr>' + 
				'<tr></tr>'	+		// for correct stripes 
				'<tr class="splits">' +
					'<td colspan="4">' +
						'<div id="collapse-'+id+'" class="accordion-body collapse" aria-labelledby="results-'+id+'">' + 
							'<table id="splits-'+id+'" class="table" style="text-align:center; background-color:transparent">' +
								'<tbody>' +
								'</tbody>' +
							'</table>' +
						'</div>' + 
					'</td>' +
				'</tr>'
			);

			//var total = 0;
			for (var j=0; j < splits.length; j++) {
				var split = Number(splits[j][0]).toFixed(3);

				// add splits to subtable
				$('table#splits-'+id+'>tbody').append(
					'<tr>' + 
						'<td class="split-number">' + (j+1) + '</td>' + 
						'<td class="split-time">' + split + '</td>' + 
						'<td class="split-edit-options hidden-xs">' +
							'<div class="modify-splits modify-splits-'+id+' pull-right" style="display:none;">' +
								'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
								'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
								'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
								'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
							'</div>' +
						'</td>' + 
					'</tr>'
				);

				// now calculate total time
				//total += Number(split);
			}

			// display total time
			total = formatTime(total);
			$('#table-canvas>tbody #results-'+id+'>td#total-time-'+id).html(total);
		}

		function toggleCorrections(enabled) {

			var status = $('#enable-corrections-status');
			if (enabled) {
				// show status
				status.css('color', '#468847');
				status.html(' Auto-correction enabled.');

				// cancel all modifications
				$('tr.modifying').find('.confirm-split .cancel-split-split').click();

				numCorrections = 0;

				// display auto-correction
				for (var i=0; i<correctionData.length; i++) {
					var runner = correctionData[i];
					var corrections = runner.results;

					for (var j=corrections.length-1; j>=0; j--) {
						var correction = corrections[j];

						splitSplit(runner.id, correction.index, correction.times);
						
						console.log(correctionData);
						numCorrections++;
					}
				}

				// add total number of corrections
				status.append(' Currently showing <span id="num-corrections">'+numCorrections+'</span> suggestions.');

			} else {
				status.css('color', '#d9534f');
				status.html(' Auto-correction disabled.');

				// cancel all modifications
				$('tr.modifying').find('.confirm-split .cancel-split-split').click();

				// re-register hover handlers
				$('body').off('mouseover', '#table-canvas>tbody>tr');
				$('body').on('mouseover', '#table-canvas>tbody>tr', function() {
					$(this).find('.modify-total-time').show();
				});
				$('body').off('mouseover', 'tr.splits table tbody tr');
				$('body').on('mouseover', 'tr.splits table tbody tr', function() {
					$(this).find('.modify-splits').show();
				});
			}
		}

		// register handler for adding runner
		$('body').on('click', 'button#add-missed-runner', function(e) {
			e.stopPropagation();

			// show warning modal
			$('.notification').hide();
			$('#add-missed-runner-modal').modal('show');

			// force numbers on input field
			$('#add-missed-runner-modal input').val('');
			forceNumeric($('input.numeric-input'));

			// show spinner
			$('#spinner-add-missed-runner').css('height', 150);
			spinner.spin(document.getElementById('spinner-add-missed-runner'));

			// request for registered runners
			$.ajax({
				method: 'GET',
				url: 'api/athletes?registered_to_session=' + '380' +
                     '&session!=' + '380',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				data: {id: currentID, missed: true },
				dataType: 'text',
				success: function(data) {
					data = $.parseJSON(data);
					console.log(data);

					if (data.length === 0) {
						// disable select
						$('#add-missed-runner-select').prop('disabled', true);

						// hide spinner and show notification
						spinner.stop();
						$('#spinner-add-missed-runner').css('height', '');
						$('.notification.no-missed-runners').show();
						$('#add-missed-runner-body').hide();
					} else {
						$('#add-missed-runner-select').prop('disabled', false);

						for (var i=0; i<data.length; i++) {
							var athlete = data[i];
							$('#add-missed-runner-select').append(
								'<option value="'+athlete.id+'">' +
                                athlete.first_name + ' ' + athlete.last_name +
                                '</option>'
							);
						}

						// hide spinner and show input form
						spinner.stop();
						$('#spinner-add-missed-runner').css('height', '');

						$('.notification.add-missed-runner').show();
						$('#add-missed-runner-body').show();

						// register handlers for button clicks
						$('body').off('click', '#add-missed-runner-confirm');
						$('body').on('click', '#add-missed-runner-confirm', function(e) {
							e.preventDefault();

							athleteID = $('#add-missed-runner-select option:selected').val();
							hrs = Number($('#add-missed-runner-hrs').val());
							mins = Number($('#add-missed-runner-mins').val());
							secs = Number($('#add-missed-runner-secs').val());
							ms = Number($('#add-missed-runner-ms').val());

							if ((mins > 59) || (secs > 59) || (ms > 999)) {
								$('.notification.add-missed-runner-error').show();
								return;
							}
                            var data = [{
                                "id": athleteID,
                                "splits": [hrs*3600 + mins*60 + secs + ms/1000.0]
                            }];

							$.ajax({
								method: 'POST',
								url: 'api/sessions/'+'380'+'/upload_results/',
								headers: {Authorization: 'Bearer ' +
                                          sessionStorage.access_token},

								data: JSON.stringify(data),
								contentType: 'application/json',
								success: function(data) {
									$('#table-canvas').empty();
									spinner.spin(target);
									update(currentID, currentView);
								},
								error: function(jqXHR, exception) {
									$('.notification.server-error').show();
								}
							});

							$('#add-missed-runner-modal').modal('hide');
						});

						$('body').off('click', '#add-missed-runner-cancel');
						$('body').on('click', '#add-missed-runner-cancel', function(e) {
							e.preventDefault();
							$('#add-missed-runner-modal').modal('hide');
						});
					}
				}
			});
		});

		// register handler for downloading results
		$('body').on('click', 'button#download', function(e) {
			e.stopPropagation();

			$('.notification').hide();
			$('#download-results-modal').modal('show');
			$('#download-results-body').show();
            $('body').off('click', '#download-results-confirm');
            $('body').on('click', '#download-results-confirm', function(e) {
                e.preventDefault();

			    $('#spinner-download-results').css('height', 150);
			    spinner.spin(document.getElementById('spinner-download-results'));

                downloadFormat = $('input[name="download-format"]:checked').val();

                $.ajax({
                    method: 'POST',
                    url: '/api/sessions/' + '380' + '/export_results/',
                    headers: {
                        Authorization: 'Bearer ' + sessionStorage.access_token
                    },
                    data: JSON.stringify({
                        'file_format': downloadFormat
                    }),
                    contentType: 'application/json',
                    dataType: 'text',
                    success: function(data) {
                        var uri = $.parseJSON(data).uri;
                        var link = document.createElement('a');
                        link.href = uri;
                        link.style = 'visibility:hidden';

                        spinner.stop();
						$('#spinner-download-results').css('height', '');
				        $('#download-results-modal').modal('hide');

                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                    },
                    error: function(jqXHR, exception) {
                    	spinner.stop();
                    	$('#spinner-download-results').css('height', '');
				        $('#download-results-modal').modal('hide');

                        $('#email-success').modal('show');
                    	$('#email-success-message').hide();
                        $('#email-failure-message').show();
                    }
                });
            });
            $('body').off('click', '#download-results-cancel');
            $('body').on('click', '#download-results-cancel', function(e) {
                e.preventDefault();
                $('#download-results-modal').modal('hide');
            });

		});

		//Register Handler for Emailing Results
				// register handler for downloading results
		$('body').on('click', 'button#email', function(e) {
			e.stopPropagation();

			$('.notification').hide();
			$('#email-results-modal').modal('show');
			$('#email-body').show();
            $('body').off('click', '#email-results-confirm');
            $('body').on('click', '#email-results-confirm', function(e) {
                e.preventDefault();

			    $('#spinner-email-results').css('height', 150);
			    spinner.spin(document.getElementById('spinner-email-results'));

                resultsBoolean = $('input[name="email-format"]:checked').val();

                $.ajax({
                    method: 'POST',
                    url: '/api/sessions/' + '380' + '/email_results/',
                    headers: {
                        Authorization: 'Bearer ' + sessionStorage.access_token
                    },
                    data: {'full_results': resultsBoolean},
                    success: function(data) {
                        spinner.stop();
						$('#spinner-email-results').css('height', '');
				        $('#email-results-modal').modal('hide');

                        $('#email-success').modal('show');
                        $('#email-failure-message').hide();
                    	$('#email-success-message').show();


                    },
                    error: function(jqXHR, exception) {
                    	spinner.stop();
                    	$('#spinner-email-results').css('height', '');
				        $('#email-results-modal').modal('hide');


                    	$('#email-success').modal('show');
                    	$('#email-success-message').hide();
                        $('#email-failure-message').show();
                    }
                });
            });
            $('body').off('click', '#email-results-cancel');
            $('body').on('click', '#email-results-cancel', function(e) {
                e.preventDefault();
                $('#email-results-modal').modal('hide');
            });

		});

		// register handler for edit total time
		$('body').on('mouseover', '#table-canvas>tbody>tr', function() {
			$(this).find('.modify-total-time').show();
		});
		$('body').on('mouseleave', '#table-canvas>tbody>tr', function() {
			$(this).find('.modify-total-time').hide();
		});
		$('body').on('click', '.modify-total-time>div', function(e) {
			e.stopPropagation();

			// stop updates
			stopUpdates();

			// show warning modal
			$('.notification').hide();
			$('.notification.edit-total').show();
			$('#modify-total-time-modal input').val('');
			$('#modify-total-time-modal').modal('show');

			var runnerID = $(this).closest('td').attr('id').split('-')[3];

			// force numbers on input field
			forceNumeric($('input.numeric-input'));

			// register handlers for button clicks
			$('body').off('click', '#modify-total-time-confirm');
			$('body').on('click', '#modify-total-time-confirm', function(e) {
				e.preventDefault();

				var hrs = Number($('#total-hrs').val()),
						mins = Number($('#total-mins').val()),
						secs = Number($('#total-secs').val()),
						ms = Number($('#total-ms').val());

				if ((mins > 59) || (secs > 59) || (ms > 999)) {
					$('.notification.total-time-error').show();
					return;
				}

				//console.log(hrs+':'+mins+':'+secs+'.'+ms);

				$.ajax({
					method: 'POST',
					url: 'api/edit_split/',
					headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
					data: { id: currentID,
									user_id: runnerID,
									action: 'total_time',
									hour: hrs,
									min: mins,
									sec: secs,
									mil: ms },
					success: function(data) {
						$('#table-canvas').empty();
						$('#spinner').css('height', 150);
						spinner.spin(target);
						update(currentID, currentView);
					},
					error: function(jqXHR, exception) {
						$('.notification.server-error').show();
					}
				});

				// hide modal
				$('#modify-total-time-modal').modal('hide');
			});

			$('body').off('click', '#modify-total-time-cancel');
			$('body').on('click', '#modify-total-time-cancel', function(e) {
				e.preventDefault();
				$('#modify-total-time-modal').modal('hide');
			});

			// start updates after modal is hidden
			$('#modify-total-time-modal').off('hidden.bs.modal');
			$('#modify-total-time-modal').on('hidden.bs.modal', function(e) {
				startUpdates();
			});
		})

		// register handler for editing splits
		$('body').on('mouseover', 'tr.splits table tbody tr', function() {
			$(this).find('.modify-splits').show();
		});
		$('body').on('mouseleave', 'tr.splits table tbody tr', function() {
			$(this).find('.modify-splits').hide();
		});
		$('body').on('click', '.modify-splits>div', function(e) {
			e.preventDefault();
			
			// prompt to disable filter choice if on
			if (sessionData.filter_choice) {
				$('#filter-disable-modal').modal('show');

				$('body').off('click', '#filter-disable-modal #filter-disable-confirm');
				$('body').on('click', '#filter-disable-modal #filter-disable-confirm', function(e) {
					e.preventDefault();

					// make ajax call to turn off filter
					$.ajax({
						type: 'PATCH',
						dataType: 'json',
						url: '/api/sessions/380/',
						headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
						data: {
							filter_choice: false,
						},
						success: function(data) {
							// update front end data
							sessionData.filter_choice = false;

							// then hide confirmation modal
							$('#filter-disable-modal').modal('hide');
						}
					});
				});

				$('body').off('click', '#filter-disable-modal #filter-disable-cancel');
				$('body').on('click', '#filter-disable-modal #filter-disable-cancel', function(e) {
					e.preventDefault();
					$('#filter-disable-modal').modal('hide');
				});
				return;
			}

			// pause updates
			stopUpdates();

			var runnerID = $(this).parent().attr('class').toString().split(' ')[1].split('-')[2].trim();
			var action = $(this).attr('class').toString().split('-')[0].trim();
			
			// set index to modify
			var indx = $(this).closest('tr').index();

			if ((action === 'insert') && ($(this).index() === 0)) {
				addSplit($(this), runnerID, indx, false);
			} else if ((action === 'insert') && ($(this).index() === 1)) {
				indx++;
				addSplit($(this), runnerID, indx, true);
			} else if (action === 'edit') {
				editSplit($(this), runnerID, indx);
			} else if (action === 'delete') {
				deleteSplit($(this), runnerID, indx);
			}
		});

		function addSplit(target, runnerID, indx, after, value) {
			var splitRow = target.closest('tr');

			// hide edit buttons
			target.parent().hide();
			$('body').off('mouseover', 'tr.splits table tbody tr');

			// html for new row
			var newSplitRow = {};
			var newSplitRowHTML = '' +
				'<tr>' + 
					'<td class="split-number">' + (indx+1) + '</td>' + 
					'<td class="split-time">' + 
						'<input type="text" id="insert-'+runnerID+'-'+indx+'" class="form-control numeric-input" placeholder="Split value" style="color:#3c763d;" autofocus>' + 
					'</td>' + 
					'<td class="split-edit-options hidden-xs">' +
						'<div class="modify-splits modify-splits-'+runnerID+' pull-right" style="display:none;">' +
							'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
							'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
							'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
							'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
						'</div>' +
						'<div class="confirm-insert pull-right">' +
							'<button value="insert" class="confirm-insert-split btn btn-sm btn-primary" style="margin-right:10px;">Save</button>' +
							'<button value="cancel" class="cancel-insert-split btn btn-sm btn-danger">Cancel</button>' +
						'</div>' +
					'</td>' + 
				'</tr>';

			if (after) {
				// add the row
				splitRow.after(newSplitRowHTML);
				newSplitRow = splitRow.next();
			} else {
				// add the row
				splitRow.before(newSplitRowHTML);
				newSplitRow = splitRow.prev();
			}

			// mark as being modified
			newSplitRow.addClass('modifying');

			// add value if supplied
			newSplitRow.find('input#insert-'+runnerID+'-'+indx).val(value);

			// update the split numbers
			var splitRowsAfter = newSplitRow.nextAll();
			for (var i=0; i<splitRowsAfter.length; i++) {
				$(splitRowsAfter[i]).find('.split-number').html( indx+2 + i );
			}

			// force numeric input
			forceNumeric(newSplitRow.find('input'));

			// autofocus to new row input field
			newSplitRow.find('input').focus();

			// highlight split row
			newSplitRow.css('background-color', '#dff0d8').css('color', '#3c763d');

			// bind click handler
			var button = newSplitRow.find('td.split-edit-options .confirm-insert button');
			newSplitRow.find('.confirm-insert').on('click', button, function(e) {
				e.preventDefault();
				if ($(e.target).attr('value') === 'insert') {
					var splitTime = newSplitRow.find('td.split-time input').val();
					splitTime = $.isNumeric(splitTime) ? Number(splitTime).toFixed(3) : '0.000';
					
					console.log('Add split value ('+splitTime+') at index ('+indx+') for runnerID ('+runnerID+') on workoutID ('+currentID+')');

					// insert in backend
					$.ajax({
						method: 'POST',
						url: 'api/edit_split/',
						headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
						data: { id: currentID,
										user_id: runnerID,
										action: 'insert',
										indx: indx,
										val: splitTime },
						success: function() {
							// remove marker
							newSplitRow.removeClass('modifying');

							// remove confirmation buttons
							newSplitRow.find('td.split-edit-options .confirm-insert').remove();

							// re-register handler if nothing else is being modified
							if ($('tr.modifying').length === 0) {
								$('body').on('mouseover', 'tr.splits table tbody tr', function() {
									$(this).find('.modify-splits').show();
								});
							}

							// restore new split row colors
							newSplitRow.css('background-color', '').css('color', '');

							// update on frontend
							newSplitRow.find('td.split-time').html(splitTime);

							var totalTimeCell = $('tr#results-'+runnerID+'>td#total-time-'+runnerID),
									prevTotalTime = convertToSeconds(totalTimeCell.html());
							totalTimeCell.html(formatTime(prevTotalTime+Number(splitTime)));

							if (newSplitRow.index() === $('table#splits-'+runnerID+' tbody tr').length-1) {
								$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(splitTime);
							}

							// restart updates
							startUpdates();
						}
					});
				} else {		// clicked cancel
					// remove marker
					newSplitRow.removeClass('modifying');

					// reset the split numbers
					splitRowsAfter = newSplitRow.nextAll();
					for (var i=0; i<splitRowsAfter.length; i++) {
						$(splitRowsAfter[i]).find('.split-number').html( indx+1 + i );
					}

					// remove added row
					newSplitRow.remove();

					// re-register handler if nothing else is being modified
					if ($('tr.modifying').length === 0) {
						$('body').on('mouseover', 'tr.splits table tbody tr', function() {
							$(this).find('.modify-splits').show();
						});
					}

					// restart updates
					startUpdates();
				}
			});
		}

		function editSplit(target, runnerID, indx, value) {
			var splitRow = target.closest('tr');

			// mark as being modified
			splitRow.addClass('modifying');

			// get split value
			var splitTimeCell = splitRow.find('td.split-time');
			var prevSplitTime = splitTimeCell.html();

			// replace split with textbox
			splitTimeCell.html('<input type="text" id="edit-'+runnerID+'-'+indx+'" class="form-control numeric-input" placeholder="Split value" style="color:#f90;" autofocus>');
			
			// force numeric input
			forceNumeric(splitTimeCell.find('input'));

			// populate textbox
			if (value === undefined)
				splitTimeCell.find('input').val(prevSplitTime).focus();
			else
				splitTimeCell.find('input').val(value).focus();

			// hide edit buttons and add save/cancel button
			target.parent().hide();
			$('body').off('mouseover', 'tr.splits table tbody tr');
			splitRow.find('td.split-edit-options').append(
				'<div class="confirm-edit pull-right">' +
					'<button value="update" class="confirm-edit-split btn btn-sm btn-primary" style="margin-right:10px;">Update</button>' +
					'<button value="cancel" class="cancel-edit-split btn btn-sm btn-danger">Cancel</button>' +
				'</div>'
			);

			// highlight split row
			splitRow.css('background-color', '#fcf8e3').css('color', '#c60');

			// bind click handler
			var button = target.find('button');
			splitRow.find('.confirm-edit').on('click', button, function(e) {
				e.preventDefault();
				if ($(e.target).attr('value') === 'update') {
					var splitTime = splitTimeCell.find('input').val();
					splitTime = $.isNumeric(splitTime) ? Number(splitTime).toFixed(3) : '0.000';
					
					console.log('Edit split value from ('+prevSplitTime+') to ('+splitTime+') at index ('+indx+') for runnerID ('+runnerID+') on workoutID ('+currentID+')');
					// edit in backend
					$.ajax({
						method: 'POST',
						url: 'api/edit_split/',
						headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
						data: { id: currentID,
										user_id: runnerID,
										action: 'edit',
										indx: indx,
										val: splitTime },
						success: function() {
							// remove marker
							splitRow.removeClass('modifying');

							// remove confirmation buttons
							splitRow.find('.confirm-edit').remove();

							// re-register handler if nothing else is being modified
							if ($('tr.modifying').length === 0) {
								$('body').on('mouseover', 'tr.splits table tbody tr', function() {
									$(this).find('.modify-splits').show();
								});
							}

							// restore split row
							splitRow.css('background-color', '').css('color', '');

							// update on frontend
							splitTimeCell.html(splitTime);

							var totalTimeCell = $('tr#results-'+runnerID+'>td#total-time-'+runnerID),
									prevTotalTime = convertToSeconds(totalTimeCell.html()),
									timeDifference = Number(splitTime) - Number(prevSplitTime);
							totalTimeCell.html(formatTime(prevTotalTime+timeDifference));

							if (splitRow.index() === $('table#splits-'+runnerID+' tbody tr').length-1) {
								$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(splitTime);
							}

							// restart updates
							startUpdates();
						}
					});
				} else {		// clicked cancel
					// remove marker
					splitRow.removeClass('modifying');

					// replace input textbox with split value
					splitTimeCell.html(prevSplitTime);

					// remove confirmation buttons
					splitRow.find('.confirm-edit').remove();

					// re-register handler if nothing else is being modified
					if ($('tr.modifying').length === 0) {
						$('body').on('mouseover', 'tr.splits table tbody tr', function() {
							$(this).find('.modify-splits').show();
						});
					}

					// restore split row
					splitRow.css('background-color', '').css('color', '');

					// restart updates
					startUpdates();
				}
			});
		}

		function deleteSplit(target, runnerID, indx) {
			var splitRow = target.closest('tr');
			var splitTimeCell = splitRow.find('td.split-time');
			var splitTime = Number(splitTimeCell.html());

			// mark as being modified
			splitRow.addClass('modifying');

			// hide edit buttons and add save/cancel button
			target.parent().hide();
			$('body').off('mouseover', 'tr.splits table tbody tr');
			splitRow.find('td.split-edit-options').append(
				'<div class="confirm-delete pull-right">' +
					'<button value="delete" class="confirm-delete-split btn btn-sm btn-danger" style="margin-right:10px;">Delete</button>' +
					'<button value="cancel" class="cancel-delete-split btn btn-sm btn-default">Cancel</button>' +
				'</div>'
			);

			// highlight split row
			splitRow.css('background-color', '#f2dede').css('color', '#d9534f');

			// bind click handler
			var button = target.find('button');
			splitRow.find('.confirm-delete').on('click', button, function(e) {
				e.preventDefault();
				if ($(e.target).attr('value') === 'delete') {

					console.log('Delete split value ('+splitTime+') at index ('+indx+') for runnerID ('+runnerID+') on workoutID ('+currentID+')');
					// delete in backend
					$.ajax({
						method: 'POST',
						url: 'api/edit_split/',
						headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
						data: { id: currentID,
										user_id: runnerID,
										action: 'delete',
										indx: indx },
						success: function() {
							// remove marker
							splitRow.removeClass('modifying');

							// remove confirmation buttons
							splitRow.find('.confirm-delete').remove();

							// re-register handler if nothing else is being modified
							if ($('tr.modifying').length === 0) {
								$('body').on('mouseover', 'tr.splits table tbody tr', function() {
									$(this).find('.modify-splits').show();
								});
							}

							// delete on frontend
							var splitRowsAfter = splitRow.nextAll();
							for (var i=0; i<splitRowsAfter.length; i++) {
								$(splitRowsAfter[i]).find('.split-number').html( indx+1 + i );
							}

							var totalTimeCell = $('tr#results-'+runnerID+'>td#total-time-'+runnerID),
									prevTotalTime = convertToSeconds(totalTimeCell.html());
							totalTimeCell.html(formatTime(prevTotalTime - splitTime));

							var splitRowsAll = $('table#splits-'+runnerID+' tbody tr')
							if (splitRow.index() === splitRowsAll.length-1) {
								var latestSplit = $('table#splits-'+runnerID+' tbody tr:nth-child('+(splitRowsAll.length-1)+')').find('td.split-time').html();
								latestSplit = latestSplit || 'NT';
								$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(latestSplit);
							}

							if (splitRow.siblings().length === 0) {
								var temp = $('#results-'+runnerID);
								temp.next().remove();
								temp.next().remove();
								temp.remove();
							} else {
								splitRow.remove();
							}

							// restart updates
							startUpdates();
						}
					});
				} else {		// clicked cancel
					// remove marker
					splitRow.removeClass('modifying');

					// remove confirmation buttons
					splitRow.find('.confirm-delete').remove();

					// re-register handler if nothing else is being modified
					if ($('tr.modifying').length === 0) {
						$('body').on('mouseover', 'tr.splits table tbody tr', function() {
							$(this).find('.modify-splits').show();
						});
					}

					// restore split row
					splitRow.css('background-color', '').css('color', '');

					// restart updates
					startUpdates();
				}
			});
		}

		function splitSplit(runnerID, indx, values) {
			var splits = $('#splits-'+runnerID+' tbody tr:not(.inserting)');
			var splitRow = $(splits[indx]);

			// mark as being modified
			splitRow.addClass('modifying');

			// replace split with textbox
			var splitTimeCell = splitRow.find('td.split-time');
			var prevSplitTime = splitTimeCell.html();
			splitTimeCell.html('<input type="text" id="split-'+runnerID+'-'+indx+'" class="form-control numeric-input" placeholder="Split value" style="color:#f90;">');

			// hide normal edit functionality
			$('body').off('mouseover', '#table-canvas>tbody>tr');
			$('body').off('mouseover', 'tr.splits table tbody tr');

			// hide edit buttons and add save/cancel button
			splitRow.find('.modify-splits').hide();
			splitRow.find('td.split-edit-options').append(
				'<div class="previous-split pull-right">' +
					'was ' + prevSplitTime +
				'</div>'
			);

			// html for new row
			var newSplitRowHTML = '' +
				'<tr class="modifying inserting">' +
					'<td class="split-number"></td>' +
					'<td class="split-time">' +
						'<input type="text" id="insert-'+runnerID+'-'+(indx+1)+'" class="form-control numeric-input" placeholder="Split value" style="color:#f90;">' + 
					'</td>' +
					'<td class="split-edit-options hidden-xs">' +
						'<div class="modify-splits modify-splits-'+runnerID+'" style="display:none;">' +
							'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
							'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
							'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
							'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
						'</div>' +
						'<div class="confirm-split pull-right">' +
							'<button value="split" class="confirm-split-split btn btn-sm btn-primary" style="margin-right:10px;">Save</button>' +
							'<button value="cancel" class="cancel-split-split btn btn-sm btn-danger">Cancel</button>' +
						'</div>' +
					'</td>' +
				'</tr>';

			// add the row
			splitRow.after(newSplitRowHTML);
			var newSplitRow = splitRow.next();
			var newSplitTimeCell = newSplitRow.find('td.split-time');

			// highlight split rows
			splitRow.css('background-color', '#fcf8e3').css('color', '#c60');
			newSplitRow.css('background-color', '#fcf8e3').css('color', '#c60');

			// get the input fields
			var splitTimeInput = splitTimeCell.find('input');
			var newSplitTimeInput = newSplitTimeCell.find('input');
			
			// populate inputs with split value
			splitTimeInput.val(values[0]);
			newSplitTimeInput.val(values[1]);

			// force numbers on input fields
			forceNumeric(splitTimeInput);
			forceNumeric(newSplitTimeInput);

			// restrict inputs to add up to previous split value
			splitTimeInput.on('input', function() {
				newSplitTimeInput.val((Number(prevSplitTime) - Number($(this).val())).toFixed(3))
			});
			newSplitTimeInput.on('input', function() {
				splitTimeInput.val((Number(prevSplitTime) - Number($(this).val())).toFixed(3))
			});

			// bind click handler
			var button = newSplitRow.find('button');
			newSplitRow.find('.confirm-split').on('click', button, function(e) {
				e.preventDefault();

				// recalculate index 
				indx = $('#splits-'+runnerID+' tbody tr:not(.inserting)').index(splitRow);

				if ($(e.target).attr('value') === 'split') {
					var splitTime = splitTimeCell.find('input').val();
					splitTime = $.isNumeric(splitTime) ? Number(splitTime).toFixed(3) : '0.000';

					var newSplitTime = newSplitTimeCell.find('input').val();
					newSplitTime = $.isNumeric(newSplitTime) ? Number(newSplitTime).toFixed(3) : '0.000';

					// make sure the splits add up to previous total
					if ((Number(splitTime) + Number(newSplitTime)).toFixed(3) == Number(prevSplitTime)) {
						console.log('Split split value from ('+prevSplitTime+') into ('+splitTime+' and '+newSplitTime+') at index ('+indx+') for runnerID ('+runnerID+') on workoutID ('+currentID+')');
						
						$.ajax({
							method: 'POST',
							url: 'api/edit_split/',
							headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
							data: { id: currentID,
											user_id: runnerID,
											action: 'split',
											indx: indx,
											val: splitTime },
							success: function() {
								// remove markers
								splitRow.removeClass('modifying');
								newSplitRow.removeClass('modifying inserting');

								// remove confirmation buttons
								newSplitRow.find('.confirm-split').remove();

								// re-register handlers if nothing else is being modified
								if ($('tr.modifying').length === 0) {
									$('body').on('mouseover', '#table-canvas>tbody>tr', function() {
										$(this).find('.modify-total-time').show();
									});
									$('body').on('mouseover', 'tr.splits table tbody tr', function() {
										$(this).find('.modify-splits').show();
									});
								}

								// remove correction from pool
								for (var i=0; i<correctionData.length; i++) {
									var runner = correctionData[i];

									if (runner.id == runnerID) {
										var corrections = runner.results;
										for (var j=0; j<corrections.length; j++) {

											if (corrections[j].index == indx)
												corrections.splice(j,1);
										}
									}
								}

								// restore split row
								splitRow.css('background-color', '').css('color', '');
								newSplitRow.css('background-color', '').css('color', '');

								// update on frontend
								splitTimeCell.html(splitTime);
								newSplitTimeCell.html(newSplitTime);

								splitRow.find('.previous-split').remove();

								newSplitRow.find('.split-number').html(indx+2);
								var splitRowsAfter = newSplitRow.nextAll(':not(.inserting)');
								for (var i=0; i<splitRowsAfter.length; i++) {
									$(splitRowsAfter[i]).find('.split-number').html(indx+3+i);
								}

								if (newSplitRow.index() === $('table#splits-'+runnerID+' tbody tr').length-1) {
									$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(newSplitTime);
								}

								// update auto-correction status
								numCorrections--;
								$('#num-corrections').html(numCorrections);
							}
						});
					} else { console.log(Number(splitTime) + Number(newSplitTime) + ' != ' + Number(prevSplitTime)); }
				} else {		// clicked cancel
					// remove marker
					splitRow.removeClass('modifying');

					// replace input textbox with split value
					splitTimeCell.html(prevSplitTime);

					// remove confirmation buttons
					splitRow.find('.previous-split').remove();

					// re-register handlers if nothing else is being modified
					if ($('tr.modifying').length === 0) {
						$('body').on('mouseover', '#table-canvas>tbody>tr', function() {
							$(this).find('.modify-total-time').show();
						});
						$('body').on('mouseover', 'tr.splits table tbody tr', function() {
							$(this).find('.modify-splits').show();
						});
					}

					// restore split row
					splitRow.css('background-color', '').css('color', '');
					newSplitRow.remove();

					// update auto-correction status
					numCorrections--;
					$('#num-corrections').html(numCorrections);
				}
			});
		}

		//==================================== GRAPH VIEW ====================================

		// attach handler for athlete toggle on graph view
		$('body').on('click', '#graph-toggle-options', function(e){
			if (e.target.id === 'all')
				if ($('#graph-toggle-options input#all').prop('checked'))
					$('#graph-toggle-options input').prop('checked', true);
				else
					$('#graph-toggle-options input').prop('checked', false);
			else if (!$('#graph-toggle-options input#'+e.target.id).prop('checked'))
				$('#graph-toggle-options input#all').prop('checked', false);

			// update view
			lastSelected();
		});

		function drawGraph(data){
			var results = data.results;

			// add toggle checkboxes 
			var toggleOptions = $('#results-graph #graph-toggle-options');

			if ($('#results-graph #graph-toggle-options label input#all').length !== 1)
				toggleOptions.append(
					'<label class="checkbox"><input type="checkbox" id="all" value="" checked>All</label>'
				);

			for (var i=0; i<results.length; i++) {
				
			}

			// show results
			$('#results-graph').show();
			$('#download-container').show();

			var data = new google.visualization.DataTable();
			data.addColumn('number', 'Split');

			var rows = []; var series = [];
			for (var i=0; i<results.length; i++) {
				var runner = results[i];

				var id = runner.id,
						name = runner.name,
						splits = runner.splits,
						numSplits = splits.length,
						skip = false;

				// create new checkbox if doesn't already exist
				if ($('#results-graph #graph-toggle-options label input#'+id).length !== 1)
					toggleOptions.append(
						'<label class="checkbox"><input type="checkbox" id="'+id+'" value="" checked>' +
							name +
						'</label>'
					);

				// create data table for google charts
				data.addColumn('number', name);
				
				// skip current runner if not toggled
				if (!$('input#'+id).prop('checked')) {
					skip = true;
					series.push({visibleInLegend: false});
				} else {
					series.push({});
				}

				for (var j=0; j < numSplits; j++) {
					// create row if doesn't exist
					if (!rows[j])
						rows[j] = [j+1];
					
					if (skip)
						rows[j][i+1] = NaN;
					else
						rows[j][i+1] = Number(splits[j][0]);
				}
			}

			// add NaN's to skipped spaces
			for (var i=0; i<rows.length; i++)
				for (var j=0; j<rows[0].length; j++)
					if (typeof rows[i][j] === 'undefined')
						rows[i][j] = NaN;

			data.addRows(rows);

			var height = 300;
			if (window.innerWidth > 768)
				height = 500;

			var options = {
				title: $('#results-title').html().split(':')[1].trim(),
				height: height,
				hAxis: { title: 'Split #', minValue: 1, viewWindow: { min: 1 } },
				vAxis: { title: 'Time'},
				axes: {
					y: {
						all: {
							format: {
								pattern: 'decimal'
							}
						}
					}
				},
				series: series,
				legend: { position: 'right' }
			};

			var chart = new google.visualization.ScatterChart(document.getElementById('graph-canvas'));
			chart.draw(data, options);
		}

		//==================================== INDIVIDUAL RESULTS VIEW ====================================

		// attach handler for individual results tab
		$('body').on('change', '#gender-select, #age-select', function(){
			drawIndividual();
		});
		//Prevent from typing any non numeric characters
		$("#age-select").keypress(function (e) {
			if (e.which != 8 && e.which != 0 && e.which != 45 &&(e.which < 48 || e.which > 57)) {
			return false;
			}
		});


		function drawIndividual() {
			$('#individual-table-canvas').empty();

			var a = $('#age-select').val();
			var g = $('#gender-select').val();
			console.log(a);

			// gender or age wasn't selected
			if ((a === null) || (g === null)) {
				$('.notification.select-group').show();
				return;
			}
			$('.notification.select-group').hide();

			$('#spinner').css('height', 150);
			spinner.spin(target);

			a = a.split('-');
			var age_gte = a[0].trim();
			var age_lte = a[1].trim();

			var gender = (g.trim() === 'Male') ? 'M' : 'F';

			$.ajax({
				url: '/api/sessions/380/individual_results/?gender='+gender+'&age_gte='+age_gte+'&age_lte='+age_lte+'&limit=150',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data).results;
					
					if (results.length === 0) {
						spinner.stop();
						$('#spinner').css('height', '');
						$('#individual-table-canvas').empty();
						$('.notification.no-individual-data').show();
						$('#download-container').hide();
					} else {
						$('.notification').hide();

						$('#individual-table-canvas').append(
							'<thead>' +
								'<tr>' +
									'<th>Place</th>' +
									'<th>Name</th>' +
									'<th>Final Time</th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>'
						);

						var runner = {};
						for (var i=0; i < results.length; i++) {
							runner = results[i];
							$('#individual-table-canvas tbody').append(
								'<tr>' +
									'<td>'+ (i+1) +'</td>' +
									'<td>'+ runner.name +'</td>' +
									'<td>'+ formatTime(Number(runner.total)) +'</td>' +
								'</tr>'
							);
						}

						// show results
						spinner.stop();
						$('#spinner').css('height', '');
						$('#individual-table-canvas').show();
						$('#download-container').show();
					}
				}
			});
		}

		//==================================== TEAM RESULTS VIEW ====================================

		function drawTeam(){
			$('.notification').hide();
			$('#team-table-canvas').empty();
			$('#spinner').css('height', 150);
			spinner.spin(target);
			$.ajax({
				url: 'api/sessions/380/team_results',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data);

					if (results.length === 0) {
						spinner.stop();
						$('#spinner').css('height', '');
						$('.notification.no-team-data').show();
						$('#results-team').show();
						return;
					}

					// create table header
					$('#team-table-canvas').append(
						'<thead>' +
							'<tr>' +
								'<th>Place</th>' +
								'<th>Team</th>' +
								'<th>Score</th>' +
							'</tr>' +
						'</thead>' +
						'<tbody>' +
						'</tbody>'
					);

					// create table rows
					for (var i=0; i<results.length; i++) {
						var team = results[i];
						var id = team.id;
						$('#team-table-canvas>tbody').append(
							'<tr id="team-'+id+'" class="accordion-toggle collapsed" data-toggle="collapse" data-parent="#team-table-canvas" data-target="#collapse-team-'+id+'" aria-expanded="false" aria-controls="collapse-team-'+id+'">' +
								'<td>' + team.place + '</td>' +
								'<td>' + team.name + '</td>' +
								'<td>' + team.score + '</td>' +
							'</tr>' +
							'<tr></tr>'	+
							'<tr class="team-runners">' +
								'<td colspan="4">' +
									'<div id="collapse-team-'+id+'" class="accordion-body collapse" aria-labelledby="team-'+id+'">' +
										'<table id="runners-team-'+id+'" class="table" style="text-align:center; background-color:transparent">' +
											'<thead>' +
												'<tr>' +
													'<th style="text-align:center;">Place</th>' +
													'<th style="text-align:center;">Name</th>' +
													'<th style="text-align:center;">Final Time</th>' +
												'</tr>' +
											'</thead>' +
											'<tbody>' +
											'</tbody>' +
										'</table>' +
									'</div>' + 
								'</td>' +
							'</tr>'
						);
						
						for (var j=0; j<team.athletes.length; j++) {
							var athlete = team.athletes[j];
							$('table#runners-team-'+id+' tbody').append(
								'<tr>' +
									'<td>' + athlete.place + '</td>' +
									'<td>' + athlete.name + '</td>' +
									'<td>' + formatTime(Number(athlete.total)) + '</td>' +
								'</tr>'
							);
						}
					}

					/*
					// rebind click handler
					$('body').off('click', '#team-table-canvas>tbody>tr.accordion-toggle');
					$('body').on('click', '#team-table-canvas>tbody>tr.accordion-toggle', function(e) {
						e.preventDefault();
						if ($(this).hasClass('collapsed')) {

							currentTeamID = this.id.slice(4);
							currentTeam = $('tr#team-'+currentTeamID+' td:nth-child(2)').html().trim();

							// clear table data
							$('#runners-team-'+currentTeamID+' tbody').empty();

							// add a spinner
							$('#collapse-team-'+currentTeamID).append(
								'<div class="spinner-container" style="position:relative; min-height:150px;">' +
									'<div id="spinner-team-'+currentTeamID+'"></div>' +
								'</div>'
							);
							teamSpinners[currentTeamID] = teamSpinners[currentTeamID] || new Spinner(opts);
							teamSpinners[currentTeamID].spin(document.getElementById('spinner-team-'+currentTeamID));

							// get team members data
							$.ajax({
								url: 'api/sessions/'+currentID+'/filtered_results',
								headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
								data: {
									team: team.name,
									offset: 0,
									limit: 5
								},
								dataType: 'text',
								success: function(runnerData) {
									var runnerResults = $.parseJSON(runnerData).results;

									// add team members to table
									var runner = {};
									for (var i=0; i < Math.min(runnerResults.length,5); i++) {
										runner = runnerResults[i];
										$('#runners-team'+currentTeamID+' tbody').append(
											'<tr>' +
												'<td>' + (i+1) + '</td>' +
												'<td>' + runner.name + '</td>' +
												'<td>' + formatTime(Number(runner.total)) + '</td>' +
											'</tr>'
										);
									}

									// remove spinner
									teamSpinners[currentTeamID].stop();
									$('#collapse-team-'+currentTeamID).find('div').remove();
								}
							});

						} else {
							teamSpinners[currentTeamID].stop();
							$('#collapse-team-'+currentTeamID).find('div').remove();
						}
					});
					//*/
	
					// stop spinner and show results
					spinner.stop();
					$('#spinner').css('height', '');
					$('#results-team').show();
					$('#download-container').show();
				}
			});
		}

		function findScores(){
			//$('#spinner').css('height', 150);
			spinner.spin(target);

			$.ajax({
				url: '/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'json',
				data: {
					offset: sessionFirst-1,
					limit: 15,
				},
				success: function(data){
					var results = data.results,
					numSessions = data.count;
					
					if ((results.length == 0) && (!$.trim($('ul.menulist').html()))) {
						$('.notification.no-sessions').show();
						$('#results-status').hide();
						spinner.stop();
						$('#spinner').css('height', '');
					} else {
						$('.notification').hide();
						$('#results-status').show();
						for (var i=0; i<results.length; i++){
							// add events to event menu
							$('ul.menulist').append('<li><a id="session-'+results[i].id+'" href="#">'+results[i].name+'</a></li>');
							idArray.push(results[i].id);
						}
						if (results.length == 15){
							$('ul.menulist').append('<li id="see-more"><a href="#">See More</a></li>');
						}

						// show most recent workout
						if (!currentID)
							currentID = idArray[0];

						$('a#session-'+currentID).click();
					}
				}
			});
		}

		function loadCalendar(){
			$('#calendar-overlay').show();
			$('#calendar').fullCalendar({
				editable: true,
				eventLimit: true, // allow "more" link when too many events
				events: calendarEvents
			});
			cStart = $('#calendar').fullCalendar('getView').intervalStart;
			cStop = $('#calendar').fullCalendar('getView').intervalEnd;
			$('#calendar-overlay').hide();
			calendarScores();
		}

		function calendarScores(){
			cStart = localISOString(cStart._d);
			cStop = localISOString(cStop._d);
			$.ajax({
				url:'/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'json',
				data: {
					offset: sessionFirst-1,
                    limit: 15,
                    start_date: cStart,
                    stop_date: cStop,
				},
				success: function(data){
					var results = data.results,
					numSessions = data.count;

					calendarEvents = [];
					for (var i=0; i<results.length; i++){
						// add events to calendar event list
						var url = results[i].id;
						var str = results[i].start_time;
						str = str.slice(0,10);
						calendarEvents.push({title : results[i].name, url : url, start : str});
					}
					$('#calendar').fullCalendar('removeEvents');
					$('#calendar').fullCalendar('addEventSource', calendarEvents);	

					$('body').off('click', '#calendar-btn');
					$('body').on('click', '#calendar-btn', function(e){
						e.preventDefault();
						$('#calendar-overlay').show();
						$('#calendar').fullCalendar('removeEvents');
						$('#calendar').fullCalendar('addEventSource', calendarEvents);
					});

					// attach handler for hiding calendar menu
					$('body').off('click', '#calendar-overlay');
					$('body').on('click', '#calendar-overlay', function(e){
						//e.preventDefault();
						var cal = $('.calendar-container');
						if (!cal.is(e.target) && cal.has(e.target).length === 0)
							$('#calendar-overlay').hide();
					});

					// unbind and rebind previous and next buttons on calendar
					$('body').off('click', 'button.fc-next-button');
					$('body').on('click','button.fc-next-button', function(e){
						e.preventDefault();
						cStart = $('#calendar').fullCalendar('getView').intervalStart;
						cStop = $('#calendar').fullCalendar('getView').intervalEnd;
						calendarScores();
					});
					$('body').off('click', 'button.fc-prev-button');
					$('body').on('click','button.fc-prev-button',function(e){
						e.preventDefault();
						cStart = $('#calendar').fullCalendar('getView').intervalStart;
						cStop = $('#calendar').fullCalendar('getView').intervalEnd;
						calendarScores();
					});

					// rebind handler for calendar event click
					$('.calendar-container').off('click','a.fc-day-grid-event');
					$('.calendar-container').on('click','a.fc-day-grid-event', function(e) {
						e.preventDefault();
						$('#calendar-overlay').hide();

						// reset canvases and set new session id
						$('.notification').hide();
						$('#results-table #table-canvas').empty();
						$('.results-tab-content').hide();
						$('#results-graph>#graph-canvas').empty();
						$('#results-graph #graph-toggle-options').empty();
						currentID = parseInt($(this).attr('href').split('#'));
						$('#spinner').css('height', 150);
						spinner.spin(target);
						update(currentID, currentView);
					});
				}
			});
		}

		// attach handler for heat menu item click
		$('body').on('click', 'ul.menulist li a', function(){
			var value = $(this).html();
			if (value == 'See More'){
				sessionFirst += 15;
				sessionLast += 15;
				$('ul.menulist li#see-more').remove();
				findScores();
			} else {
				var indexClicked = $( 'ul.menulist li a' ).index( $(this) );
				
				// reset canvases and set new session id
				$('.notification').hide();
				$('#results-table #table-canvas').empty();
				$('.results-tab-content').hide();
				$('#results-graph>#graph-canvas').empty();
				$('#results-graph #graph-toggle-options').empty();
				$('#download-container').hide();
				currentID = idArray[indexClicked];

				// request for new session data
				if (ajaxRequest)
					ajaxRequest.abort();

				ajaxRequest = $.ajax({
					url: '/api/sessions/380',
					headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
					dataType: 'text',
					success: function(data) {
						var json = $.parseJSON(data);

						// add heat name
						//$('#results-title').html('Results: ' + 'Swinging Bridge 8k');

						// hide auto-correction options
						$('#correction-options').hide();

						$('#spinner').css('height', 150);
						spinner.spin(target);
						update(currentID, currentView);

						// update status
						if (new Date() > new Date(json.stop_time)) {
							// session is closed
							$('#results-status>span').html('&#11044;');
							$('#results-status>span').css('color', '#d9534f');
							stopUpdates();

							// show options
							$('#correction-options').show();
							$('#enable-corrections').prop('checked', false);

							// create switchery checkbox
							$('#enable-corrections').next('.switchery').remove();
							switcheryTarget = $('#enable-corrections')[0];
							switchery = new Switchery(switcheryTarget, { size: 'small', disabled: true });

							//switchery = new Switchery(elem, { size: 'small' });
							$('#enable-corrections-status').css('color', '#d9534f');
							$('#enable-corrections-status').html(' Auto-correction disabled.');

							// make ajax call for corrections
							if (correctionAjaxRequest)
								correctionAjaxRequest.abort();
							
							correctionAjaxRequest = $.ajax({
								method: 'POST', 
								url: '/stats/analyze/',
								headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
								dataType: 'json',
								data: {
									id: currentID,
								},
								success: function(data) {
									// save data and enable toggle switch
									correctionData = data;
									switchery.enable();

									// register handler for correction enabling
									$('body').off('change', '#enable-corrections');
									$('body').on('change', '#enable-corrections', function() {
										toggleCorrections($(this).prop('checked'));
									});
								}
							});
						} else {
							// session still active
							$('#results-status>span').html('&#11044;');
							$('#results-status>span').css('color', '#5cb85c');
						}

						// save session data
						sessionData = json;
					}
				});
			}
		});

		// register handler for tab navigation
		$('body').on('click', '#results>ul>li', function(e){
			e.preventDefault();
			// update tab navbar
			currentView = $(this).index();
			$(this).parent().children().removeClass('active');
			$(this).addClass('active');

			$('.notification').hide();
			$('.results-tab-content').hide();
			$('#download-container').hide();
			$('#spinner').css('height', 150);
			spinner.spin(target);

			// views 0 and 1 = live results updated every 5 secs
			if (currentView < 1) {
				// stop updates
				stopUpdates();

				// update view
				lastSelected();

				// restart updates
				startUpdates();

			} else {
				// stop updates
				stopUpdates();

				// update view
				lastSelected();
			}
		});

		// register handler for results pagination
		$('body').on('click', 'button.prev', function(e){
			e.preventDefault();

			if (currentPage != 1) {
				resultOffset -= RESULTS_PER_PAGE;
				currentPage--;
			}

			// clear table and update
			$('#table-canvas').empty();
			update(currentID, currentView);
		});

		$('body').on('click', 'button.next', function(e){
			e.preventDefault();

			resultOffset += RESULTS_PER_PAGE;
			currentPage++;

			// clear table and update
			$('#table-canvas').empty();
			update(currentID, currentView);
		});

		// download to CSV script
		/*$('body').on('click', '#download', function(){
			// hide download buttons and show status
			$('#download-container').hide();
			$('#download-status').show();

			if ((currentView === TABLE_VIEW) || (currentView === GRAPH_VIEW))
				createFullCSV();
			else if (currentView === IND_FINAL_VIEW)
				createFilteredCSV();
			else if (currentView === TEAM_FINAL_VIEW)
				createTeamCSV();
		});
		$('body').on('click', '#download-TFRRS', function(){
			// hide download buttons and show status
			$('#download-container').hide();
			$('#download-status').show();

			$.ajax({
				url: '/api/sessions/'+currentID+'/tfrrs',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					data = $.parseJSON(data);

					CSV = '';
					for (var i=0; i<data.length; i++)
						CSV += data[i] + '\r\n';
					
					download(CSV, sessionData.name+' TFRRS');

					// hide status and show download buttons
					$('#download-status').hide();
					$('#download-container').show();
				}
			});
		});*/

		//=================================== download functions ====================================
		function createFullCSV(){
			$.ajax({
				url: '/api/sessions/380/individual_results',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {

					var reportTitle = sessionData.name + ' Full Results';
					
					// initialize file content
					var CSV = '';

					// set report title in first row or line
					CSV += reportTitle + '\r\n\r\n';

					// format date and time
					var d = new Date(UTC2local(sessionData.start_time));

					CSV += 'Date,'+ d.toDateString() +'\r\n';
					CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\r\n';

					CSV += 'Track Size,'+ sessionData.track_size +'\r\n';
					CSV += 'Interval Distance,'+ sessionData.interval_distance +'\r\n\r\n';

					CSV += 'Name\r\n';


					var results = $.parseJSON(data).results;

					// iterate into results array
					for (var i=0; i < results.length; i++) {
						var runner = results[i];

						CSV += runner.name + ',';

						for (var j=0; j < runner.splits.length; j++) {
							//iterate over interval to get to nested time arrays
							var splits = runner.splits[j];

							for (var k=0; k < runner.splits[j].length; k++) {
								//interate over subarrays and pull out each individually and print
								//do a little math to move from seconds to minutes and seconds
								var subinterval = runner.splits[j][k];
								CSV += subinterval;

								if (j != runner.splits.length-1)
									CSV += ',';
							}
						}

						CSV += '\r\n';
					}

					// if variable is empty, alert invalid and return
					if (CSV == '') {        
						alert('Invalid data');
						return;
					}

					download(CSV, reportTitle);

					// hide status and show download buttons
					$('#download-status').hide();
					$('#download-container').show();
				}
			});
		}

		function createFilteredCSV() {
			var a = $('#age-select').val();
			var g = $('#gender-select').val();

			// gender or age wasn't selected
			if ((a === null) || (g === null))
				return;

			ages = a.split('-');
			var age_gte = ages[0].trim();
			var age_lte = ages[1].trim();

			var gender = (g.trim() === 'Male') ? 'M' : 'F';

			$.ajax({
				url: '/api/sessions/380/individual_results/?gender='+gender+'&age_gte='+age_gte+'&age_lte='+age_lte+'&limit=150',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data).results;

					var reportTitle = sessionData.name + ' Filtered Results';
					
					// initialize file content
					var CSV = '';

					// set report title in first row or line
					CSV += reportTitle + '\r\n\n';

					// format date and time
					var d = new Date(UTC2local(sessionData.start_time));

					CSV += 'Date,'+ d.toDateString() +'\r\n';
					CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\n';

					// add group info
					CSV += 'Gender,' + g + '\r\n';
					CSV += 'Age bracket,' + a + '\r\n\n';

					if (results.length != 0) {
						CSV += 'Place,Name,Final Time\r\n';

						for (var i=0; i < results.length; i++) {
							var runner = results[i];
							CSV += (i+1) + ',' + runner.name + ',' + formatTime(Number(runner.total)) + '\r\n';
						}
					}

					download(CSV, reportTitle);

					// hide status and show download buttons
					$('#download-status').hide();
					$('#download-container').show();
				}
			});
		}

		function createTeamCSV() {
			$.ajax({
				url: 'api/sessions/380/team_results',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data);

					var reportTitle = sessionData.name + ' Team Results';
					
					// initialize file content
					var CSV = '';

					// set report title in first row or line
					CSV += reportTitle + '\r\n\n';

					// format date and time
					var d = new Date(UTC2local(sessionData.start_time));

					CSV += 'Date,'+ d.toDateString() +'\r\n';
					CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\n';

					if (results.length != 0) {
						CSV += 'Place,Name,Score\r\n';

						for (var i=0; i < results.length; i++) {
							var team = results[i];
							CSV += team.place + ',' + team.name + ',' + team.score + '\r\n';
						}
					}

					download(CSV, reportTitle);

					// hide status and show download buttons
					$('#download-status').hide();
					$('#download-container').show();
				}
			});
		}

		/*function download(CSV, reportTitle) {
			//Generate a file name
			var fileName = 'TRAC_';
			//this will remove the blank-spaces from the title and replace it with an underscore
			fileName += reportTitle.replace(/ /g,'_');

			//Initialize file format you want csv or xls
			var uri = 'data:text/csv;charset=utf-8,' + escape(CSV);

			// Now the little tricky part.
			// you can use either>> window.open(uri);
			// but this will not work in some browsers
			// or you will not get the correct file extension

			//this trick will generate a temp <a /> tag
			var link = document.createElement('a');    
			link.href = uri;

			//set the visibility hidden so it will not effect on your web-layout
			link.style = 'visibility:hidden';
			link.download = fileName + '.csv';

			//this part will append the anchor tag and remove it after automatic click
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		}*/
		//=================================== searchbar functions ====================================
		var bool = 1;
    	$("#basic-search").click(function(){
    		if(bool==0){
        		$( "#searchinput" ).animate({
        			width:'0',
        			marginLeft:'100%',
        			paddingRight:0,
        			paddingLeft:0,
        		},1000);
        		$( "#searchclear" ).animate({
        			opacity:0
        		},1000);
    			bool = 1;
    			return;
    		}
    		else(bool==1)
    		{
    			$( "#searchinput" ).animate({
    				width:'100%',
    				marginLeft:0,
    				paddingRight:'12px',
    				paddingLeft:'12px',
    			},1000);
    			$( "#searchclear" ).animate({
    				opacity:1
    			},1000);
    			bool=0;
    			return;
    		}
    	});
    	$("#searchinput").on('input', function(){
    		drawIndividualSearch();
    	});

    	function drawIndividualSearch() {
			$('#individual-table-canvas').empty();
			$('.notification.select-group').hide();

			$('#spinner').css('height', 150);
			spinner.spin(target);

			searchTerm = $('#searchinput').val();

			$.ajax({
				url: '/api/athletes/?session=380&search='+searchTerm,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data);
					if (results.length === 0) {
						spinner.stop();
						$('#spinner').css('height', '');
						$('#individual-table-canvas').empty();
						$('.notification.no-individual-data').show();
						$('#download-container').hide();
					} else {
						$('.notification').hide();

						$('#individual-table-canvas').append(
							'<thead>' +
								'<tr>' +
									'<th>Name</th>' +
									'<th></th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>'
						);

						var runner = {};
						for (var i=0; i < results.length; i++) {
							runner = results[i];
							$('#individual-table-canvas>tbody').append(
								'<tr id="results-'+runner.id+'" class="accordion-toggle" data-toggle="collapse" data-parent="#table-canvas" data-target="#collapse-'+runner.id+'" aria-expanded="false" aria-controls="collapse-'+runner.id+'">' + 
									'<td>' + runner.first_name +' '+ runner.last_name  + '</td>' + 
									'<td id="total-time-'+runner.id+'">'+ '<a id="resultsLink-'+runner.id+'" style="cursor:pointer">See Results</a>' +'</td>' + 
										'<div class="modify-total-time pull-right" style="display:none;">' +
											'<div class="edit-total"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
										'</div>' +
									'</td>' +
								'</tr>' + 
								'<tr></tr>'	+		// for correct stripes 
								'<tr class="splits">' +
									'<td colspan="4">' +
										'<div id="collapse-'+runner.id+'" class="accordion-body collapse" aria-labelledby="results-'+runner.id+'">' + 
											'<table id="splits-'+runner.id+'" class="table" style="text-align:center; background-color:transparent">' +
												'<tbody>' +
												'</tbody>' +
											'</table>' +
										'</div>' + 
									'</td>' +
								'</tr>'
							);
							$("#resultsLink-"+runner.id).on('click', function(){
				    			//Sent the binder, load the data
				    			var dynamicID = $(this).attr('id').split('-')[1];
				    			$('table#splits-'+dynamicID+'>tbody').empty();

				    			$.ajax({
									url: '/api/sessions/380/individual_results/?athletes='+dynamicID,
									headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
									dataType: 'text',
									success: function(data) {
										var total =0;
										var splits = $.parseJSON(data).results[0].splits;
										console.log(splits);
										for (var j=0; j < splits.length; j++) {
											console.log(splits[j]);
											console.log(runner.id);
											//console.log($'$this')
											$('table#splits-'+dynamicID+'>tbody').append(
													'<tr>' + 
														'<td class="split-number">' + (j+1) + '</td>' + 
														'<td class="split-time">' + splits[j] + '</td>' + 
														'<td class="split-edit-options hidden-xs">' +
															'<div class="modify-splits modify-splits-'+runner.id+' pull-right" style="display:none;">' +
																'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
																'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
																'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
																'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
															'</div>' +
														'</td>' + 
													'</tr>'
												);
										}
									}
								});
				    	});


						}

						// show results
						spinner.stop();
						$('#spinner').css('height', '');
						$('#individual-table-canvas').show();
						$('#download-container').show();
					}
				}
			});
		};

		



	});
});
