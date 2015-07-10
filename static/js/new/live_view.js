// setup Google charts api
google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function() {
		var TABLE_VIEW = 0,
				GRAPH_VIEW = 1,
				IND_FINAL_VIEW = 2,
				TEAM_FINAL_VIEW = 3;

		var UPDATE_INTERVAL = 5000,				// update live results every 5 secs
				IDLE_TIMEOUT = 1200000;				// idle check after 20 minutes

		var idArray = [],
				currentID, currentView,												// used to identify current session and view
				updateHandler, idleHandler,										// interval handlers
				spinner, opts, target, teamSpinners = {},			// spinner variables
				currentTeamID, currentTeam,										// used in team results tab
				calendarEvents,																// holds list of sessions formatted for fullcalendar
				sessionFirst = 1, sessionLast = 15,						// used for sessions pagination
				cStart, cStop;																// used for date-based sessions query

		(function init(){

			// initialize spinner
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
				position: 'absolute'	 	// Element positioning
			}
			target = document.getElementById('spinner');
			spinner = new Spinner(opts);

			// default view to table
			currentView = TABLE_VIEW;

			// hide notifications and results
			$('.notification').hide();
			$('#results-nav').hide();
			$('.results-tab-content').hide();
			$('#download-container').hide();

			// query for all workout sessions
			spinner.spin(target);
			findScores();
			loadCalendar();

			// start updates
			startUpdates();
		})();

		function startUpdates() {
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
			var last_url = '/api/sessions/'+ idjson;
			
			//start ajax request
			$.ajax({
				url: last_url,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				success: function(data) {
					var json = $.parseJSON(data);

					/*
	      	json = {
						"id": 24, 
						"name": "E9 - Boys Heat 2", 
						"start_time": "2015-06-05T18:34:14Z", 
						"stop_time": "2015-06-06T18:34:14Z", 
						"comment": null, 
						"rest_time": 0, 
						"track_size": 400, 
						"interval_distance": 200, 
						"interval_number": 0, 
						"filter_choice": false, 
						"manager": "alsal", 
						"results": "{\"date\": \"06.05.2015\", \"runners\": [{\"counter\": [1, 2, 3], \"id\": 22, \"name\": \"Max Denning\", \"interval\": [[\"64.83\"], [\"65.05\"], [\"140.015\"]]}, {\"counter\": [1, 2, 3, 4], \"id\": 18, \"name\": \"Michael Ronzone\", \"interval\": [[\"65.477\"], [\"69.653\"], [\"79.168\"], [\"79.696\"]]}], \"workoutID\": 24}", 
						"athletes": "[\"MaxDenning\", \"MichaelRonzone\"]", 
						"start_button_time": "2015-06-06T01:29:29Z", 
						"private": true
					};
					//*/
					var results = $.parseJSON(json.results);

					// add heat name
					$('#results-title').html('Live Results: ' + json.name);

					// if empty, hide spinner and show notification
					if (results.runners == '') {
						spinner.stop();
						$('.notification.no-data').show();
						$('#download-container').hide();
						$('#results-nav').hide();
						$('.results-tab-content').hide();
						$('#results-table #table-canvas').empty();
						$('#results-graph #graph-canvas').empty();
						$('#results-graph #graph-toggle-options').empty();
					} else {
						spinner.stop();
						$('.notification').hide();
						$('#results-nav').show();

						// hide all tab contents
						$('.results-tab-content').hide();

						if (view === TABLE_VIEW) {
							$('#results-graph #graph-canvas').empty();
							$('#results-graph #graph-toggle-options').empty();
							drawTable(json);
						} else if (view === GRAPH_VIEW) {
							$('#results-table #table-canvas').empty();
							drawGraph(json);
						} else if (view === IND_FINAL_VIEW) {
							$('#results-table #table-canvas').empty();
							$('#results-graph #graph-canvas').empty();
							$('#results-graph #graph-toggle-options').empty();
							$('#results-individual').show();
							drawIndividual();
						} else if (view === TEAM_FINAL_VIEW) {
							$('#results-table #table-canvas').empty();
							$('#results-graph #graph-canvas').empty();
							$('#results-graph #graph-toggle-options').empty();
							drawTeam();
						}
					}
				}
			});
		}

		//==================================== TABLE VIEW ====================================

		function drawTable(json){
			var results = $.parseJSON(json.results);
			//*
			// add table skeleton if empty
			if (!$.trim($('#table-canvas').html())) {
				$('#table-canvas').append(
					'<thead>' + 
						'<tr>' +
							'<th>Name</th>' +
							'<th>Latest Split</th>' +
							'<th>Total Time</th>' +
						'</tr>' +
					'</thead>' +
					'<tbody id="">' +
					'</tbody>'
				);
			}

			for (var i=0; i < results.runners.length; i++) {
				var id = results.runners[i].id;
				var name = results.runners[i].name;
				var interval = results.runners[i].interval;

				// check if row exists
				var row = $('#table-canvas>tbody>tr#results-'+id);
				if (row.length === 1) {
					var numDisplayedSplits = $('table#splits-'+id+'>tbody>tr').length;
					// update splits table
					if (interval.length > numDisplayedSplits) {
						var totalTime = $('#total-time-'+id).html().split(':');
						var total = Number(totalTime[0])*60 + Number(totalTime[1]);
						
						// add the new splits if not already displayed
						for (var j=numDisplayedSplits; j < interval.length; j++) {
							var split = String(Number(interval[j][0]).toFixed(3));
							$('table#splits-'+id+'>tbody').append(
								'<tr>' + 
									'<td class="split-number col-md-2 col-sm-2">' + (j+1) + '</td>' + 
									'<td class="split-time col-md-7 col-sm-7">' + split + '</td>' + 
									'<td class="split-edit-options col-md-3 col-sm-3 hidden-xs">' +
										'<div class="modify-splits modify-splits-'+id+'" style="display:none;">' +
											'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
											'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
											'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
											'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
										'</div>' +
									'</td>' + 
								'</tr>'
							);
							total += Number(split);
						}

						// then update latest split and recalculate total
						$('#latest-split-'+id).html(String(Number(interval[interval.length-1][0]).toFixed(3)));
						$('#total-time-'+id).html(formatTime(total));
					}
				} else {
					addNewRow(id, name, interval);
				}
			}

			// show results
			$('#results-table').show();
			$('#download-container').show();
		}

		function addNewRow(id, name, interval){
			var split = 0;
			if (interval.length > 0)
				split = String(Number(interval[interval.length-1][0]).toFixed(3));
			else
				split = 'NT';

			$('#table-canvas>tbody').append(
				'<tr id="results-'+id+'" class="accordion-toggle" data-toggle="collapse" data-parent="#table-canvas" data-target="#collapse-'+id+'" aria-expanded="false" aria-controls="collapse-'+id+'">' + 
					'<td>' + name + '</td>' + 
					'<td id="latest-split-'+id+'">' + split + '</td>' + 
					'<td id="total-time-'+id+'"></td>' + 
				'</tr>' + 
				'<tr></tr>'	+		// for correct stripes 
				'<tr class="splits">' +
					'<td colspan="3">' +
						'<div id="collapse-'+id+'" class="accordion-body collapse" aria-labelledby="results-'+id+'">' + 
							'<table id="splits-'+id+'" class="table" style="text-align:center; background-color:transparent">' +
								'<tbody>' +
								'</tbody>' +
							'</table>' +
						'</div>' + 
					'</td>' +
				'</tr>'
			);

			//*
			var total = 0;
			for (var j=0; j < interval.length; j++) {
				var split = String(Number(interval[j][0]).toFixed(3));

				// add splits to subtable
				$('table#splits-'+id+'>tbody').append(
					'<tr>' + 
						'<td class="split-number col-md-2 col-sm-2">' + (j+1) + '</td>' + 
						'<td class="split-time col-md-7 col-sm-7">' + split + '</td>' + 
						'<td class="split-edit-options col-md-3 col-sm-3 hidden-xs">' +
							'<div class="modify-splits modify-splits-'+id+'" style="display:none;">' +
								'<div class="insert-split"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>' +
								'<div class="insert-split"><span class="glyphicon glyphicon-arrow-down" aria-hidden="true"></span></div>' +
								'<div class="edit-split"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></div>' +
								'<div class="delete-split"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>' +
							'</div>' +
						'</td>' + 
					'</tr>'
				);

				// now calculate total time
				total += Number(split);
			}

			// display total time
			total = formatTime(total);
			$('#table-canvas>tbody #results-'+id+'>td#total-time-'+id).html(total);
			//*/
		}

		// register handler for editing splits
		$('body').on('mouseover', 'tr.splits table tbody tr', function() {
			$(this).find('.modify-splits').show();
		});
		$('body').on('mouseleave', 'tr.splits table tbody tr', function() {
			$(this).find('.modify-splits').hide();
		});
		$('body').on('click', '.modify-splits>div', function(e) {
			e.preventDefault();
			
			// pause updates 
			stopUpdates();

			var runnerID = $(this).parent().attr('class').toString().split(' ')[1].split('-')[2].trim();
			var action = $(this).attr('class').toString().split('-')[0].trim();
			
			// set index to modify
			var indx = $(this).closest('tr').index();

			if ((action === 'insert') && ($(this).index() === 0)) {
				addSplit($(this), runnerID, indx, false);
			} else if ((action === 'insert') && ($(this).index() === 1)) {
				addSplit($(this), runnerID, indx, true);
			} else if (action === 'edit') {
				editSplit($(this), runnerID, indx);
			} else if (action === 'delete') {
				deleteSplit($(this), runnerID, indx);
			}
		});

		

		function editSplit(target, runnerID, indx) {
			var splitRow = target.closest('tr');

			// get split value
			var splitTimeCell = splitRow.find('td.split-time');
			var prevSplitTime = splitTimeCell.html();

			// replace split with textbox
			splitTimeCell.html('<input type="text" id="edit-'+runnerID+'-'+indx+'" class="form-control" placeholder="Split value" style="color:#f90;" autofocus>');
			splitTimeCell.find('input').val(prevSplitTime).focus();

			// hide edit buttons and add save/cancel button
			target.parent().hide();
			$('body').off('mouseover', 'tr.splits table tbody tr');
			target.closest('td').append(
				'<div class="confirm-edit" style="display: table; margin: 0 auto;">' +
					'<button value="update" class="confirm-edit-split btn btn-sm btn-primary" style="margin-right:10px;">Update</button>' +
					'<button value="cancel" class="cancel-edit-split btn btn-sm btn-danger">Cancel</button>' +
				'</div>'
			);

			// highlight split row
			splitRow.css('background-color', '#fcf8e3').css('color', '#c60');

			// bind click handler
			var button = target.find('button');
			target.closest('td').find('.confirm-edit').on('click', button, function(e) {
				e.preventDefault();
				if ($(e.target).attr('value') === 'update') {
					var splitTime = splitTimeCell.find('input').val();
					splitTime = $.isNumeric(splitTime) ? String(Number(splitTime).toFixed(3)) : '0.000';
					
					console.log('Confirm edit split for workout '+currentID+', runner '+runnerID+', split number '+indx+' with value '+splitTime);

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
							// remove confirmation buttons
							target.closest('td').find('.confirm-edit').remove();

							// re-register handler
							$('body').on('mouseover', 'tr.splits table tbody tr', function() {
								$(this).find('.modify-splits').show();
							});

							// restore split row
							splitRow.css('background-color', '').css('color', '');

							// update on frontend
							splitTimeCell.html(splitTime);

							var totalTimeCell = $('tr#results-'+runnerID+'>td#total-time-'+runnerID),
									prevTotalTime = convertToSeconds(totalTimeCell.html()),
									timeDifference = Number(splitTime) - Number(prevSplitTime);
							totalTimeCell.html(formatTime(prevTotalTime+timeDifference));

							if (splitTimeCell.closest('tr').index() === $('table#splits-'+runnerID+' tbody tr').length-1) {
								$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(splitTime);
							}

							// restart updates
							startUpdates();
						}
					});
				} else {		// clicked cancel
					// replace input textbox with split value
					splitTimeCell.html(prevSplitTime);

					// remove confirmation buttons
					target.closest('td').find('.confirm-edit').remove();

					// re-register handler
					$('body').on('mouseover', 'tr.splits table tbody tr', function() {
						$(this).find('.modify-splits').show();
					});

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

			// hide edit buttons and add save/cancel button
			target.parent().hide();
			$('body').off('mouseover', 'tr.splits table tbody tr');
			target.closest('td').append(
				'<div class="confirm-delete" style="display: table; margin: 0 auto;">' +
					'<button value="delete" class="confirm-delete-split btn btn-sm btn-danger" style="margin-right:10px;">Delete</button>' +
					'<button value="cancel" class="cancel-delete-split btn btn-sm btn-default">Cancel</button>' +
				'</div>'
			);

			// highlight split row
			splitRow.css('background-color', '#f2dede').css('color', '#d9534f');

			// bind click handler
			var button = target.find('button');
			target.closest('td').find('.confirm-delete').on('click', button, function(e) {
				e.preventDefault();
				if ($(e.target).attr('value') === 'delete') {
					//*
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
							// remove confirmation buttons
							target.closest('td').find('.confirm-delete').remove();

							// re-register handler
							$('body').on('mouseover', 'tr.splits table tbody tr', function() {
								$(this).find('.modify-splits').show();
							});

							// delete on frontend
							var splitRowsAfter = splitRow.nextAll();
							for (var i=0; i<splitRowsAfter.length; i++) {
								$(splitRowsAfter[i]).find('.split-number').html( indx+1 + i );
							}

							var splitTime = Number(splitTimeCell.html());
							var totalTimeCell = $('tr#results-'+runnerID+'>td#total-time-'+runnerID),
									prevTotalTime = convertToSeconds(totalTimeCell.html());
							totalTimeCell.html(formatTime(prevTotalTime - splitTime));

							var splitRowsAll = $('table#splits-'+runnerID+' tbody tr')
							if (splitTimeCell.closest('tr').index() === splitRowsAll.length-1) {
								var latestSplit = $('table#splits-'+runnerID+' tbody tr:nth-child('+(splitRowsAll.length-1)+')').find('td.split-time').html();
								$('tr#results-'+runnerID+'>td#latest-split-'+runnerID).html(latestSplit);
							}

							splitRow.remove();

							// restart updates
							startUpdates();
						}
					});
					//*/
				} else {		// clicked cancel
					// remove confirmation buttons
					target.closest('td').find('.confirm-delete').remove();

					// re-register handler
					$('body').on('mouseover', 'tr.splits table tbody tr', function() {
						$(this).find('.modify-splits').show();
					});

					// restore split row
					splitRow.css('background-color', '').css('color', '');

					// restart updates
					startUpdates();
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

		function drawGraph(json){
			var results = $.parseJSON(json.results);

			// add toggle checkboxes 
			var toggleOptions = $('#results-graph #graph-toggle-options');

			if ($('#results-graph #graph-toggle-options label input#all').length !== 1)
				toggleOptions.append(
					'<label class="checkbox"><input type="checkbox" id="all" value="" checked>All</label>'
				);

			for (var i=0; i<results.runners.length; i++) {
				var id = results.runners[i].id;
				// create new checkbox if doesn't already exist
				if ($('#results-graph #graph-toggle-options label input#'+id).length !== 1)
					toggleOptions.append(
						'<label class="checkbox"><input type="checkbox" id="'+id+'" value="" checked>' +
							results.runners[i].name +
						'</label>'
					);
			}

			// show results
			$('#results-graph').show();
			$('#download-container').show();

			var data = new google.visualization.DataTable();
			data.addColumn('number', 'Split');

			var rows = []; var series = [];
			for (var i=0; i<results.runners.length; i++) {
				var id = results.runners[i].id;
				var name = results.runners[i].name;
				var interval = results.runners[i].interval;
				var numSplits = interval.length;
				var skip = false;

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
						rows[j][i+1] = Number(interval[j][0]);
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
			  title: json.name,
			  height: height,
			  hAxis: { title: 'Split #', minValue: 1, viewWindow: { min: 1 } },
			  vAxis: { title: 'Time'},
			  //hAxis: {title: 'Split', minValue: 0, maxValue: 10},
			  //vAxis: {title: 'Time', minValue: 50, maxValue: 100},
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

		function drawIndividual() {
			$('#individual-table-canvas').empty();

			var a = $('#age-select').val();
			var g = $('#gender-select').val();

			// gender or age wasn't selected
			if ((a === null) || (g === null)) {
				$('.notification.select-group').show();
				return;
			}
			$('.notification.select-group').hide();

			spinner.spin(target);

			a = a.split('-');
			var age_gte = a[0].trim();
			var age_lte = a[1].trim();

			var gender = (g.trim() === 'Male') ? 'M' : 'F';

			$.ajax({
				url: '/api/filtered_results/?id='+currentID+'&gender='+gender+'&age_gte='+age_gte+'&age_lte='+age_lte,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data).results;

					if (results == '') {
						spinner.stop();
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
									'<td>'+ runner.place +'</td>' +
									'<td>'+ runner.name +'</td>' +
									'<td>'+ formatTime(Number(runner.time)) +'</td>' +
								'</tr>'
							);
						}

						// show results
						spinner.stop();
						$('#individual-table-canvas').show();
						$('#download-container').show();
					}
				}
			});
		}

		//==================================== TEAM RESULTS VIEW ====================================

		function drawTeam(){
			$('#team-table-canvas').empty();
			spinner.spin(target);
			$.ajax({
				url: 'api/team_results/?id='+currentID,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(data) {
					var results = $.parseJSON(data).results;

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
					var team = {};
					for (var i=0; i < results.length; i++) {
						team = results[i];
						var id = team.id;
						$('#team-table-canvas>tbody').append(
							'<tr id="team'+id+'" class="accordion-toggle collapsed" data-toggle="collapse" data-parent="#team-table-canvas" data-target="#collapse-team'+id+'" aria-expanded="false" aria-controls="collapse-team'+id+'">' +
								'<td>' + team.place + '</td>' +
								'<td>' + team.name + '</td>' +
								'<td>' + team.score + '</td>' +
							'</tr>' +
							'<tr></tr>'	+
							'<tr class="team-runners">' +
								'<td colspan="3">' +
									'<div id="collapse-team'+id+'" class="accordion-body collapse" aria-labelledby="team'+id+'">' +
										'<table id="runners-team'+id+'" class="table" style="text-align:center; background-color:transparent">' +
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
					}

					// rebind click handler
					$('body').off('click', '#team-table-canvas>tbody>tr.accordion-toggle');
					$('body').on('click', '#team-table-canvas>tbody>tr.accordion-toggle', function(e) {
						e.preventDefault();
						if ($(this).hasClass('collapsed')) {

							currentTeamID = this.id.slice(4);
							currentTeam = $('tr#team'+currentTeamID+' td:nth-child(2)').html().trim();

							// clear table data
							$('#runners-team'+currentTeamID+' tbody').empty();

							// add a spinner
							$('#collapse-team'+currentTeamID).append(
								'<div class="spinner-container" style="position:relative; min-height:150px;">' +
									'<div id="spinner-team'+currentTeamID+'"></div>' +
								'</div>'
							);
							teamSpinners[currentTeamID] = teamSpinners[currentTeamID] || new Spinner(opts);
							teamSpinners[currentTeamID].spin(document.getElementById('spinner-team'+currentTeamID));

							// get team members data
							$.ajax({
								url: 'api/filtered_results/?id='+currentID+'&team='+currentTeam,
								headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
								dataType: 'text',
								success: function(runnerData) {
									var runnerResults = $.parseJSON(runnerData).results;

									// add team members to table
									var runner = {};
									for (var i=0; i < runnerResults.length; i++) {
										runner = runnerResults[i];
										$('#runners-team'+currentTeamID+' tbody').append(
											'<tr>' +
												'<td>' + runner.place + '</td>' +
												'<td>' + runner.name + '</td>' +
												'<td>' + formatTime(Number(runner.time)) + '</td>' +
											'</tr>'
										);
									}

									// remove spinner
									teamSpinners[currentTeamID].stop();
									$('#collapse-team'+currentTeamID).find('div').remove();
								}
							});

						} else {
							teamSpinners[currentTeamID].stop();
							$('#collapse-team'+currentTeamID).find('div').remove();
						}
					});
	
					// stop spinner and show results
					spinner.stop();
					$('#results-team').show();
					$('#download-container').show();
				}
			});
		}

		function findScores(){
			//spinner.spin(target);

			$.ajax({
				url: '/api/session_Pag/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				data: {
					i1: sessionFirst,
					i2: sessionLast,
				},
				success: function(data){
					var json = $.parseJSON(data);
					
					if ((json.length == 0) && (!$.trim($('ul.menulist').html()))) {
						$('.notification.no-sessions').show();
						spinner.stop();
					} else {
						$('.notification').hide();
						for (var i=json.length-1; i >= 0; i--){
							// add events to event menu
							$('ul.menulist').append('<li><a href="#">'+json[i].name+'</a></li>');
							idArray.push(json[i].id);
						}
						if (json.length == 15){
							$('ul.menulist').append('<li id="see-more"><a href="#">See More</a></li>');
						}
					}
					// show most recent workout
					currentID = currentID || idArray[0];
					update(currentID, currentView);
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
				url:'/api/session_Pag/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				data: {
					i1: 0, i2: 0, start_date: cStart, stop_date: cStop,
				},
				success: function(data){
					var json = $.parseJSON(data);
					calendarEvents = [];
					for (var i=0; i < json.length; i++){
						// add events to calendar event list
						var url = json[i].id;
						var str = json[i].start_time;
						str = str.slice(0,10);
						calendarEvents.push({title : json[i].name, url : url, start : str});
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
				currentID = idArray[indexClicked];
				spinner.spin(target);
				update(currentID, currentView);
			}
		});

		// attach handler for tab navigation
		$('body').on('click', '#results>ul>li', function(e){
			e.preventDefault();
			// update tab navbar
			currentView = $(this).index();
			$(this).parent().children().removeClass('active');
			$(this).addClass('active');

			$('.notification').hide();
			$('.results-tab-content').hide();
			$('#download-container').hide();
			spinner.spin(target);

			// views 0 and 1 = live results updated every 5 secs
			if (currentView < 1) {
				// update view
				lastSelected();

				// restart updates
				stopUpdates();
				startUpdates();

			} else {
				// stop updates
				stopUpdates();

				// update view
				lastSelected();
			}
		});

		//Download to Excel Script
		$('body').on('click', '#download', function(){
			if ((currentView === TABLE_VIEW) || (currentView === GRAPH_VIEW))
				createFullCSV(currentID);
			else if (currentView === IND_FINAL_VIEW)
				createFilteredIndividualCSV(currentID);
			else if (currentView === TEAM_FINAL_VIEW)
				createFilteredTeamCSV(currentID);
		});
	});
});

function createFullCSV(idjson){
	$.ajax({
		url: '/api/sessions/'+idjson,
		headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
		dataType: 'text',
		success: function(data) {
			var json = $.parseJSON(data);

			var reportTitle = json.name + ' Full Results';
			
			// initialize file content
			var CSV = '';

			// set report title in first row or line
			CSV += reportTitle + '\r\n\n';

			// format date and time
			var d = new Date(UTC2local(json.start_time));

			CSV += 'Date,'+ d.toDateString() +'\r\n';
			CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\n';

			CSV += 'Name\r\n';

			var results = $.parseJSON(json.results);
			

			// iterate into runner array
			var runner = {};
			for (var i=0; i < results.runners.length; i++) {
				runner = results.runners[i];

				CSV += runner.name + ',';

				for (var j=0; j < runner.interval.length; j++) {
					//iterate over interval to get to nested time arrays
					var interval = runner.interval[j];

					for (var k=0; k < results.runners[i].interval[j].length; k++) {
						//interate over subarrays and pull out each individually and print
						//do a little math to move from seconds to minutes and seconds
						var subinterval = results.runners[i].interval[j][k];
						CSV += subinterval+',';
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
		}
	});
}

function createFilteredIndividualCSV(idjson) {
	$.ajax({
		url: '/api/sessions/'+idjson,
		headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
		dataType: 'text',
		success: function(data) {
			var json = $.parseJSON(data);

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
				url: '/api/filtered_results/?id='+idjson+'&gender='+gender+'&age_gte='+age_gte+'&age_lte='+age_lte,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(filteredData) {
					var filteredResults = $.parseJSON(filteredData).results;

					var reportTitle = json.name + ' Individual Results';
					
					// initialize file content
					var CSV = '';

					// set report title in first row or line
					CSV += reportTitle + '\r\n\n';

					// format date and time
					var d = new Date(UTC2local(json.start_time));

					CSV += 'Date,'+ d.toDateString() +'\r\n';
					CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\n';

					// add group info
					CSV += 'Gender,' + g + '\r\n';
					CSV += 'Age bracket,' + a + '\r\n\n';

					if (filteredResults != '') {
						CSV += 'Place,Name,Final Time\r\n';

						var runner = {};
						for (var i=0; i < filteredResults.length; i++) {
							runner = filteredResults[i];
							CSV += runner.place + ',' + runner.name + ',' + formatTime(Number(runner.time)) + '\r\n';
						}
					}

					download(CSV, reportTitle);
				}
			});
		}
	});
}

function createFilteredTeamCSV(idjson) {
	$.ajax({
		url: '/api/sessions/'+idjson,
		headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
		dataType: 'text',
		success: function(data) {
			var json = $.parseJSON(data);

			$.ajax({
				url: '/api/team_results/?id='+idjson,
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',
				success: function(teamData) {
					var teamResults = $.parseJSON(teamData).results;

					var reportTitle = json.name + ' Team Results';
					
					// initialize file content
					var CSV = '';

					// set report title in first row or line
					CSV += reportTitle + '\r\n\n';

					// format date and time
					var d = new Date(UTC2local(json.start_time));

					CSV += 'Date,'+ d.toDateString() +'\r\n';
					CSV += 'Time,'+ d.toLocaleTimeString() +'\r\n\n';

					if (teamResults != '') {
						CSV += 'Place,Name,Score\r\n';

						var team = {};
						for (var i=0; i < teamResults.length; i++) {
							team = teamResults[i];
							CSV += team.place + ',' + team.name + ',' + team.score + '\r\n';
						}
					}

					download(CSV, reportTitle);
				}
			});
		}
	});
}

function download(CSV, reportTitle) {
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
}