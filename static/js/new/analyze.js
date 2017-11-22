google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function(){
		//===================================== CONSTANTS & variables =====================================
		var TABLE_VIEW = 0,
				GRAPH_VIEW = 1;

		var baseData, compareData,
				currentView = TABLE_VIEW;

		//===================================== spinner configuration =====================================
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
		var spinner = new Spinner(opts);
		var target = $('#spinner')[0];

		//======================================= initialize page =========================================
		(function init() {
			loadAthletes();

			// register handler for athlete selection
			$('.workout-select').prop('disabled', true);
			$('body').on('change', '.athlete-select', function() {
				// get selected athlete ID
				var id = $(this).val();
				var target = $(this).closest('.row').find('.workout-select');
				var isBase = $(this).attr('id') == 'base-athlete-select';
				
				loadSessions(id, target, isBase);
			});

			// register handler for workout selection
			$('body').on('change', '.workout-select', function() {

				update();
			});

			// register handler for tab click
			$('body').on('click', 'ul#results-nav>li', function(e) {
				e.preventDefault();
				// update tab navbar
				if ($(this).hasClass('active'))
					return;

				$(this).parent().children().removeClass('active');
				$(this).addClass('active');

				// get index of tab and update respectively
				currentView = $(this).index();
				
				update();
			});
		})();

		//===================================== analyze.js functions ======================================
		function loadAthletes() {
			// show spinner
			$('#spinner').css('height', 150);
			spinner.spin(target);

			// hide notifications
			$('.notification').hide();

			// reset content
			$('#results').hide();

			$.ajax({
				type: 'GET',
				url: '/api/athletes/?primary_team=True',
				headers: {Authorization: 'Bearer ' + localStorage.access_token},
				dataType: 'json',
				success: function(data) {
					if (data.length === 0) {
						// hide spinner and show notification
						spinner.stop();
						$('#spinner').css('height', '');
						$('.notification.no-athletes').show();
						return;
					} 

					for (var i=0; i<data.length; i++) {
						$('#base-athlete-select').append(
							'<option value="'+data[i].id+'">' +
								data[i].first_name + ' ' + data[i].last_name +
							'</option>'
						);

						$('#compare-athlete-select').append(
							'<option value="'+data[i].id+'">' +
								data[i].first_name + ' ' + data[i].last_name +
							'</option>'
						);
					}

					// hide spinner and show notification
					spinner.stop();
					$('#spinner').css('height', '');
					$('.notification.select-sessions').show();

					// show options and results
					$('#compare-options').show();
					$('#results').show();
				}
			});
		}

		function loadSessions(athleteID, target, isBase) {
			// clear workout select options
			target.children().first().nextAll().remove();

			$.ajax({
				type: 'GET',
				url: '/api/athletes/'+athleteID+'/completed_sessions/',
				headers: {Authorization: 'Bearer ' + localStorage.access_token},
				dataType: 'json',
				success: function(data) {
					if (isBase)
						baseData = data;
					else
						compareData = data;

					var sessions = data.sessions;

					for (var i=0; i<sessions.length; i++) {
						target.append(
							'<option value="'+sessions[i].id+'">' +
								sessions[i].name +
							'</option>'
						);
					}

					// enable workout select
					target.prop('disabled', false);
				}
			});
		}

		function update() {
			// don't do anything if user hasn't select workouts to compare
			if (!$('#base-workout-select').val() || !$('#compare-workout-select').val())
				return;

			// hide notifications
			$('.notification').hide();

			// get the correct session data
			var baseSession = baseData.sessions[$('#base-workout-select option:selected').index()-1],
					compareSession = compareData.sessions[$('#compare-workout-select option:selected').index()-1];

			// update results based on view
			if (currentView === TABLE_VIEW)
				drawTable(baseSession, compareSession)
			else if (currentView === GRAPH_VIEW)
				drawGraph(baseSession, compareSession)
		}

		function drawTable(baseSession, compareSession) {
			// reset content
			$('.results-tab-content').hide();
			$('#splits-table').empty();

			// show spinner
			$('#spinner').css('height', 150);
			spinner.spin(target);

			$('#splits-table').append(
				'<thead>' + 
					'<tr>' +
						'<th>Split</th>' +
						'<th>'+baseData.name+'</th>' +
						'<th>'+compareData.name+'</th>' +
					'</tr>' +
				'</thead>' +
				'<tbody>' +
				'</tbody>'
			);

			// get splits
			var baseSplits = baseSession.splits,
					compareSplits = compareSession.splits;

			var numSplits = Math.max(baseSplits.length, compareSplits.length);

			// populate table with splits
			for (var i=0; i<numSplits; i++) {
				var baseSplit = baseSplits[i] ? baseSplits[i] : 'NT',
						compareSplit = compareSplits[i] ? compareSplits[i] : 'NT';

				$('#splits-table tbody').append(
					'<tr>' +
						'<td width="10%">'+(i+1)+'</td>' +
						'<td width="45%">'+baseSplit+'</td>' +
						'<td width="45%">'+compareSplit+'</td>' +
					'</tr>'
				);
			}

			// hide spinner
			spinner.stop();
			$('#spinner').css('height', '');

			// show results
			$('#results-table').show();
		}

		function drawGraph(baseSession, compareSession) {
			// reset content
			$('.results-tab-content').hide();
			$('#graph-canvas').empty();

			// show spinner
			$('#spinner').css('height', 150);
			spinner.spin(target);

			// get label and splits
			var baseLabel = $('#base-athlete-select option:selected').text() + ' - ' + baseSession.name,
					compareLabel = $('#compare-athlete-select option:selected').text() + ' - ' + compareSession.name;

			var baseSplits = baseSession.splits,
					compareSplits = compareSession.splits;

			// init graph and add the columns
			var graph = new google.visualization.DataTable();
			graph.addColumn('number', 'Split');
			graph.addColumn('number', baseLabel);
			graph.addColumn('number', compareLabel);

			// add the splits
			var numSplits = Math.max(baseSplits.length, compareSplits.length);
			for (var i=0; i<numSplits; i++) {
				var row = [i+1];

				if (baseSplits[i])
					row.push(Number(baseSplits[i]));
				else
					row.push(NaN);

				if (compareSplits[i])
					row.push(Number(compareSplits[i]));
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

			$('#results-graph').show();
			var chart = new google.visualization.ScatterChart(document.getElementById('graph-canvas'));
			chart.draw(graph, options);

			// hide spinner
			spinner.stop();
			$('#spinner').css('height', '');
		}
	});
});
