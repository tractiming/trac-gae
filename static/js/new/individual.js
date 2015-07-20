google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function(){

		var spinner, opts, target,					// spinner variables
				baseData, compareData;					// saved data for compare tab


		//===================================== spinner configuration =====================================
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
			position: 'relative'	 	// Element positioning
		}
		target = document.getElementById('spinner');
		spinner = new Spinner(opts);
		


		loadIndividual();

		function loadIndividual() {
			// show spinner
			$('#spinner').css('height', 150);
			spinner.spin(target);

			// reset content
			$('.results-tab-content').hide();
			$('#results-table #workouts-table tbody').empty();

			$.ajax({
				type: 'GET',
				url: '/api/individual_splits/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'json',
				data: {
					id: athleteID,
				},
				success: function(data){
					var name = data.name,
							sessions = data.sessions;

					$('#athlete-title').html(name);

					if (sessions.length == 0) {
						return;
					}

					for(i=0; i<sessions.length; i++) {
						var name = sessions[i].name,
								date = new Date(sessions[i].date).toString().slice(0,25),
								id = sessions[i].id,
								interval = sessions[i].runner.interval;
						
						addNewRow(id, date, name, interval);
					}

					// hide spinner
					spinner.stop();
					$('#spinner').css('height', '');

					// show results
					$('#results-table').show();
				}
			});
		}

		function addNewRow(id, date, name, interval){
			var split = 0;
			if (interval.length > 0)
				split = interval[interval.length-1][0];
			else
				split = 'NT';

			$('#workouts-table>tbody').append(
				'<tr id="results'+id+'" class="accordion-toggle" data-toggle="collapse" data-parent="#workouts-table" data-target="#collapse'+id+'" aria-expanded="false" aria-controls="collapse'+id+'">' + 
					'<td>' + name + '</td>' +  
					'<td>' + date + '</td>' +
					'<td id="total-time'+id+'"></td>' + 
				'</tr>' + 
				'<tr></tr>' +   // for correct stripes 
				'<tr class="splits">' +
					'<td colspan="3" style="padding: 0px;">' +
						'<div id="collapse'+id+'" class="accordion-body collapse" aria-labelledby="results'+id+'">' + 
							'<table id="splits'+id+'" class="table" style="text-align:center; background-color:transparent">' +
								'<tbody>' +
								'</tbody>' +
							'</table>' +
						'</div>' + 
					'</td>' +
				'</tr>'
			);

			//*
			var total = 0;
			for (var j=0; j<interval.length; j++) {
				var split = String(Number(interval[j][0]).toFixed(3));

				// add splits to subtable
				$('table#splits'+id+'>tbody').append(
					'<tr>' + 
						'<td>' + (j+1) + '</td>' + 
						'<td>' + split + '</td>' + 
					'</tr>'
				);

				// now calculate total time
				total += Number(split);
			}

			// display total time
			total = formatTime(String(total));
			$('#workouts-table>tbody #results'+id+'>td#total-time'+id).html(total);
			//*/
		}

		function graphIndividual() {
			// show spinner
			$('#spinner').css('height', 150);
			spinner.spin(target);

			// show corrent content
			$('.results-tab-content').hide();
			$('#graph-canvas').empty();
			$('#graph-toggle-container').hide();
			$('#results-graph').show();

			$.ajax({
				type: 'GET',
				url: '/api/individual_splits/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'json',
				data: {
					id: athleteID,
				},
				success: function(data){
					var name = data.name,
							sessions = data.sessions;

					if (sessions.length == 0) {
						return;
					}

					var toggleOptions = $('#results-graph #graph-toggle-options');

					if ($('#results-graph #graph-toggle-options label input#all').length !== 1)
						toggleOptions.append(
							'<label class="checkbox"><input type="checkbox" id="all" value="" checked>All</label>'
						);

					for (var i=0; i<sessions.length; i++) {
						var id = sessions[i].id;
						// create new checkbox if doesn't already exist
						if ($('#results-graph #graph-toggle-options label input#'+id).length !== 1)
							toggleOptions.append(
								'<label class="checkbox"><input type="checkbox" id="'+id+'" value="" checked>' +
									sessions[i].name +
								'</label>'
							);
					}

					// draw graph
					var graph = new google.visualization.DataTable();
					graph.addColumn('number', 'Split');

					var rows = []; var series = [];

					for (var i=0; i<sessions.length; i++) {
						var id = sessions[i].id;
						var name = sessions[i].name;
						var interval = sessions[i].runner.interval;
						var numSplits = interval.length;
						var skip = false;

						graph.addColumn('number', name);

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

					graph.addRows(rows);

					var height = 300;
					if (window.innerWidth > 768)
						height = 500;

					var options = {
						title: name,
						height: height,
						hAxis: { title: 'Split #', minValue: 1, viewWindow: { min: 1 } },
						vAxis: { title: 'Time'},
						//hAxis: {title: 'Split', minValue: 0, maxValue: 10},
						//vAxis: {title: 'Time', minValue: 50, maxValue: 100},
						series: series,
						legend: { position: 'right' }
					};

					var chart = new google.visualization.ScatterChart(document.getElementById('graph-canvas'));
					chart.draw(graph, options);

					// hide spinner and show results
					spinner.stop();
					$('#spinner').css('height', '');

					$('#graph-toggle-container').show();
				}
			});
		}

		function compareIndividual() {
			// show correct content
			$('.results-tab-content').hide();
			$('#results-compare').show();

			// clear select options
			$('.workout-select option:nth-child(1)').nextAll().remove();
			$('.athlete-select option:nth-child(1)').nextAll().remove();

			$.ajax({
				type: 'GET',
				url: '/api/individual_splits/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'json',
				data: {
					id: athleteID,
				},
				success: function(data) {
					baseData = data;

					var name = data.name,
							sessions = data.sessions;

					$('#base-athlete-select').append('<option disabled selected>'+name+'</option>');

					for (var i=0; i<sessions.length; i++) {
						$('#base-workout-select').append('<option value="'+sessions[i].id+'">'+sessions[i].name+'</option>');
					}

					$.ajax({
						type: 'GET',
						url: '/api/athletes/',
						headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
						dataType: 'json',
						success: function(data2) {
							for (var i=0; i<data2.length; i++) {
								$('#compare-athlete-select').append(
									'<option value="'+data2[i].id+'">' +
										data2[i].first_name + ' ' + data2[i].last_name +
									'</option>'
								);
							}
						}
					});

					// register handler for compare athlete select
					$('body').off('change', '#compare-athlete-select');
					$('body').on('change', '#compare-athlete-select', function() {
						// get selected athlete ID
						var id = $('#compare-athlete-select').val();

						// clear workout select options
						$('#compare-workout-select option:nth-child(1)').nextAll().remove();

						$.ajax({
							type: 'GET',
							url: '/api/individual_splits/',
							headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
							dataType: 'json',
							data: {
								id: id,
							},
							success: function(data) {
								compareData = data;

								var sessions = data.sessions;

								for (var i=0; i<sessions.length; i++) {
									$('#compare-workout-select').append(
										'<option value="'+sessions[i].id+'">' +
											sessions[i].name +
										'</option>'
									);
								}
							}
						});
					});
				}
			});
	
			// register handler for selecting workouts for comparison
			$('body').off('change', '#results-compare select');
			$('body').on('change', '#results-compare select', function() {
				// clear graph
				$('#compare-graph-canvas').empty();

				// don't do anything if user hasn't select workouts to compare
				if (!$('#base-workout-select').val() || !$('#compare-workout-select').val())
					return;

				// show spinner
				$('#spinner').css('height', 150);
				spinner.spin(target);

				// get the correct session data
				var baseSession = baseData.sessions[$('#base-workout-select option:selected').index()-1],
						compareSession = compareData.sessions[$('#compare-workout-select option:selected').index()-1];

				var baseLabel = baseSession.runner.name + ' - ' + baseSession.name,
						compareLabel = compareSession.runner.name + ' - ' + compareSession.name;

				var baseSplits = baseSession.runner.interval,
						compareSplits = compareSession.runner.interval;

				// init graph and add the columns
				var graph = new google.visualization.DataTable();
				graph.addColumn('number', 'Split');
				graph.addColumn('number', baseLabel);
				graph.addColumn('number', compareLabel);

				// add the splits
				var numSplits = (baseSplits.length > compareSplits.length) ? baseSplits.length : compareSplits.length;
				for (var i=0; i<numSplits; i++) {
					var row = [i+1];

					if (baseSplits[i])
						row.push({v: Number(baseSplits[i][0]), f: baseSplits[i][0]})
					else
						row.push(NaN);

					if (compareSplits[i])
						row.push(Number(compareSplits[i][0]))
					else
						row.push(NaN);

					graph.addRow(row);
				}

				var height = 300;
				if (window.innerWidth > 768)
					height = 500;

				var options = {
					title: 'Comparison',
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
					legend: { position: 'right' }
				};

				var chart = new google.visualization.ScatterChart(document.getElementById('compare-graph-canvas'));
				chart.draw(graph, options);

				// hide spinner
				spinner.stop();
				$('#spinner').css('height', '');
			});
		}

		$('body').on('click', 'ul#results-nav>li', function(e) {
			e.preventDefault();
			// update tab navbar
			$(this).parent().children().removeClass('active');
			$(this).addClass('active');

			// get index of tab and update respectively
			var index = $(this).index();
			if (index == 0)
				loadIndividual();
			else if (index == 1)
				graphIndividual();
			else if (index == 2)
				compareIndividual();
		});

		// attach handler for athlete toggle on graph view
		$('body').on('click', '#graph-toggle-options', function(e) {
			if (e.target.id === 'all')
				if ($('#graph-toggle-options input#all').prop('checked'))
					$('#graph-toggle-options input').prop('checked', true);
				else
					$('#graph-toggle-options input').prop('checked', false);
			else if (!$('#graph-toggle-options input#'+e.target.id).prop('checked'))
				$('#graph-toggle-options input#all').prop('checked', false);

			// update graph
			graphIndividual();
		});
	});
});