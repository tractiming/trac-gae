google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function(){
		
		loadIndividual();

		function loadIndividual() {
			// show correct content
			$('.results-tab-content').hide();
			$('#results-table #workouts-table tbody').empty();
			$('#results-table').show();

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
							sessions = data.sessions.reverse();

					$('#athlete-title').html(name);

					for(i=0; i<sessions.length; i++) {
						var name = sessions[i].name,
								date = new Date(sessions[i].date).toString().slice(0,25),
								id = sessions[i].id,
								interval = sessions[i].runner.interval;
						
						addNewRow(id, date, name, interval);
					}
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
			// show corrent content
			$('.results-tab-content').hide();
			$('#graph-canvas').empty();
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
							sessions = data.sessions.reverse();

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
				}
			});
		}

		function compareIndividual() {
			$('.results-tab-content').hide();
			$('#results-compare').show();
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