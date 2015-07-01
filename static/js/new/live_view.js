// setup Google charts api
google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(function(){
	$(function() {
		var TABLE_VIEW = 0,
				CAL_VIEW = 1;

		var UPDATE_INTERVAL = 5000, 
				IDLE_TIMEOUT = 1200000;

		var idArray = [],
				currentID, currentView,
				updateHandler, idleHandler,
				spinner,
				target,
				calendarEvents,
				graphToggle;

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

			// default view to table
			currentView = TABLE_VIEW;

			// hide all notifications
			$('.notification').hide();
			$('#results-nav').hide();
			$('#results-table').hide();
			$('#results-graph').hide();
			$('#download-container').hide();

			// query for all workout sessions
			findScores();

			// display most recent results
			lastWorkout();

			// refresh the view every 5 seconds to update
			updateHandler = setInterval(lastSelected, UPDATE_INTERVAL);

			// idle check after 20 minutes
			idleHandler = setTimeout(function(){ idleCheck(updateHandler, lastSelected, UPDATE_INTERVAL, IDLE_TIMEOUT, 'http://www.trac-us.com'); }, IDLE_TIMEOUT);
		})();

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
						$('#notifications .notification-default').show();
						$('#download-container').hide();
						$('#results-nav').hide();
						$('#results-table').hide().empty();
						$('#results-graph').hide();
						$('#results-graph>#graph-canvas').empty();
						$('#results-graph #graph-toggle-options').empty();
					} else {
						spinner.stop();
						$('#notifications .notification-default').hide();
						$('#download-container').show();
						$('#results-nav').show();

						if (view === TABLE_VIEW) {
							$('#results-graph').hide();
							$('#results-graph>#graph-canvas').empty();
							$('#results-graph #graph-toggle-options').empty();
							drawTable(json);
						} else if (view === CAL_VIEW) {
							$('#results-table').hide().empty();
							drawGraph(json);
						}
					}
				}
			});
		}

		function drawTable(json){
			var results = $.parseJSON(json.results);

			// show table
			$('#results-table').show();

			//*
			// add table skeleton if empty
			if (!$.trim($('#results-table').html())) {
				$('#results-table').append(
					'<thead>' + 
						'<tr>' +
							'<th>Name</th>' +
							'<th>Latest Split</th>' +
							'<th>Total Time</th>' +
						'</tr>' +
					'</thead>' +
					'<tbody>' +
					'</tbody>'
				);
			}

			for (var i=0; i < results.runners.length; i++) {
				var id = results.runners[i].id;
				var name = results.runners[i].name;
				var interval = results.runners[i].interval;

				var row = $('#results-table>tbody>tr#results'+id);
				// check if row exists
				if (row.length === 1) {
					var numDisplayedSplits = $('table#splits'+id+'>tbody>tr').length;
					// update splits table
					if (interval.length > numDisplayedSplits) {
						var totalTime = $('#total-time'+id).html().split(':');
						var total = Number(totalTime[0])*60 + Number(totalTime[1]);
						
						// add the new splits if not already displayed
						for (var j=numDisplayedSplits; j < interval.length; j++) {
							var split = String(Number(interval[j][0]).toFixed(3));
							$('table#splits'+id+'>tbody').append(
								'<tr>' + 
									'<td>' + (j+1) + '</td>' + 
									'<td>' + split + '</td>' + 
								'</tr>'
							);
							total += Number(split);
						}

						// then update latest split and recalculate total
						$('#latest-split'+id).html(interval[interval.length-1][0]);
						$('#total-time'+id).html(formatTime(total));
					}
				} else {
					addNewRow(id, name, interval);
				}
			}
		}

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

			// show graph
			$('#results-graph').show();

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
			  title: 'Split Times',
			  height: height,
			  hAxis: { title: 'Split', minValue: 1, viewWindow: { min: 1 } },
			  vAxis: { title: 'Time'},
			  //hAxis: {title: 'Split', minValue: 0, maxValue: 10},
			  //vAxis: {title: 'Time', minValue: 50, maxValue: 100},
			  series: series,
			  legend: { position: 'right' }
			};

			var chart = new google.visualization.ScatterChart(document.getElementById('graph-canvas'));
			chart.draw(data, options);
		}

		function addNewRow(id, name, interval){
			var split = 0;
			if (interval.length > 0)
				split = interval[interval.length-1][0];
			else
				split = 'NT';

			$('#results-table>tbody').append(
				'<tr id="results'+id+'" class="accordion-toggle" data-toggle="collapse" data-parent="#results-table" data-target="#collapse'+id+'" aria-expanded="false" aria-controls="collapse'+id+'">' + 
					'<td>' + name + '</td>' + 
					'<td id="latest-split'+id+'">' + split + '</td>' + 
					'<td id="total-time'+id+'"></td>' + 
				'</tr>' + 
				'<tr></tr>'	+		// for correct stripes 
				'<tr class="splits">' +
					'<td colspan="3">' +
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
			for (var j=0; j < interval.length; j++) {
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
			$('#results-table>tbody #results'+id+'>td#total-time'+id).html(total);
			//*/
		}

		function lastWorkout(){
			$.ajax({
				url: '/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				success: function(data){
					var json = $.parseJSON(data);
					//alert(json.length);
					if (json.length==0){ 
						$('#notifications notification-default2').show();
						spinner.stop();
					} else {
						$('#notifications notification-default2').hide();
						var idjson = json[json.length - 1].id;
						update(idjson, currentView);
						currentID = idjson;						
					}
				}
			});
		}
		
		function lastSelected(){
			$.ajax({
				url: '/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				success: function(data){
					var json = $.parseJSON(data);
					//alert(json.length);
					if (json.length==0){ 
						$('#notifications notification-default2').show();
						spinner.stop();
					} else {
						$('#notifications notification-default2').hide();
						update(currentID, currentView);
					}
				}
			});
		}
			
		function findScores(){
			$.ajax({
				url: '/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				success: function(data){
					var json = $.parseJSON(data);
					//alert(json.length);
					if (json.length==0){ 
						$('#notifications notification-default2').show();
						spinner.stop();
					} else {
						$('#notifications notification-default2').hide();
						var arr = [];
						calendarEvents = [];
						for (var i=0; i < json.length; i++){
							// add events to event menu
							$('#linkedlist').append('<tr><td>'+json[i].name+'</td></tr>');
							$('ul.menulist').append('<li><a href="#">'+json[i].name+'</a></li>');
							arr.push(json[i].id);

							// add events to calendar event list
							var url = json[i].id;
							var str = json[i].start_time;
							str = str.slice(0,10);
							calendarEvents.push({title : json[i].name, url : url, start : str});
						}
						idArray = arr;
					}
				}
			});
		}

		// attach handler for heat menu item click
		$('body').on('click', 'ul.menulist li a', function(){
			var value = $(this).html();
			console.log( 'Index: ' + $( 'ul.menulist li a' ).index( $(this) ) );
			var indexClicked = $( 'ul.menulist li a' ).index( $(this) );

			// reset canvases and set new session id
			$('.notification').hide();
			$('#results-table').hide().empty();
			$('#results-graph').hide();
			$('#results-graph>#graph-canvas').empty();
			$('#results-graph #graph-toggle-options').empty();
			currentID = idArray[indexClicked];
			spinner.spin(target);
			update(currentID, currentView);
		});
		
		//Download to Excel Script
		$('#download').click(function(){
			$.ajax({
				url: '/api/sessions/',
				headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
				dataType: 'text',			//force to handle it as text
				success: function(data){
					urlfn(currentID);
					return currentID;
				}
			});
		});

		// attach handler for calendar menu click
		$('#calendar-btn').click(function(e){
			e.preventDefault();

			$('#calendar-overlay').show();
			// Calendar script
			$('#calendar').fullCalendar({
				editable: true,
				eventLimit: true, // allow "more" link when too many events
				events: calendarEvents //calls list from function above
			});
		});

		// attach handler for hiding calendar menu
		$('#calendar-overlay').click(function(e){
			//e.preventDefault();
			var cal = $('.calendar-container');
			if (!cal.is(e.target) && cal.has(e.target).length === 0)
				$('#calendar-overlay').hide();
		});

		// attach handler for calendar event click
		$('.calendar-container').on('click','a.fc-day-grid-event', function(e) {
			e.preventDefault();
			$('#calendar-overlay').hide();

			// reset canvases and set new session id
			$('.notification').hide();
			$('#results-table').hide().empty();
			$('#results-graph').hide()
			$('#results-graph>#graph-canvas').empty();
			$('#results-graph #graph-toggle-options').empty();
			currentID = parseInt($(this).attr('href').split('#'));
			spinner.spin(target);
			update(currentID, currentView);
		});

		// attach handler for tab navigation
		$('#results>ul>li').click(function(e){
			e.preventDefault();
			// update tab navbar
			currentView = $(this).index();
			$(this).parent().children().removeClass('active');
			$(this).addClass('active');

			$('#results-table').hide();
			$('#results-graph').hide();
			$('#download-container').hide();
			spinner.spin(target);

			// update view
			lastSelected();

			// clear and reset update handler
			clearInterval(updateHandler);
			updateHandler = setInterval(lastSelected, UPDATE_INTERVAL);

			// clear and reset idle check
			clearTimeout(idleHandler);
			idleHandler = setTimeout(function(){ idleCheck(updateHandler, lastSelected, UPDATE_INTERVAL, IDLE_TIMEOUT, 'http://www.trac-us.com'); }, IDLE_TIMEOUT);
		});

		$('#graph-toggle-options').click(function(e){
			if (e.target.id === 'all')
				if ($('#graph-toggle-options input#all').prop('checked'))
					$('#graph-toggle-options input').prop('checked', true);
				else
					$('#graph-toggle-options input').prop('checked', false);

			// update view
			lastSelected();
		});
	});
});

// format time in seconds to mm:ss.mil
function formatTime(timeStr) {
	var time = Number(timeStr);
	var mins = Math.floor(time / 60);
	var secs = (time % 60).toFixed(3);
	secs = Math.floor(secs / 10) == 0 ? '0'+secs : secs;
	return mins.toString() + ':' + secs.toString();
}

function urlfn(idjson){
	var last_url = '/api/sessions/'+ idjson;
	//alert(last_url);
	$.ajax({
		url: last_url,
		headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
		dataType: 'text',			//force to handle it as text
		success: function(data) {
			JSONToCSVConvertor(data, 'TRAC_Report', true);
		}
	});
}

function JSONToCSVConvertor(JSONData, ReportTitle, ShowLabel) {
	//Data coming in must be json
	//parse through it
	var json = $.parseJSON(JSONData);
	//now json variable contains data in json format
	//let's display a few items
	// $('#results').html('Date: ' + json.date);
	//$('#results').append('<p> Workout ID: '+ json.workoutID);

	var CSV = '';
	//Set Report title in first row or line
	CSV += ReportTitle + '\r\n\n';
	CSV += 'Date,'+ json.start_time+'\r\n';
	CSV += 'Workout ID,'+ json.id+'\r\n\n';

	CSV += 'Name \r\n'
	
	//Uncomment below when using nested json in production
	json = $.parseJSON(json.results);

	//iterate into name array
	for (var i=0; i < json.runners.length; i++) {
		//print names and enter name array
		var name = json.runners[i].name;
		CSV +=name+',';

		for (var j=0; j < json.runners[i].interval.length; j++) {
			//iterate over interval to get to nested time arrays
			var interval = json.runners[i].interval[j];

			for (var k=0; k < json.runners[i].interval[j].length; k++) {
				//interate over subarrays and pull out each individually and print
				//do a little math to move from seconds to minutes and seconds
				var subinterval = json.runners[i].interval[j][k];
				var min = Math.floor(subinterval/60);
				var sec = (subinterval-(min*60));
				CSV += subinterval+',';

				/*
				//This if statements adds the preceding 0 to any second less than 10
				if (sec<10)
					CSV += min + ':0'+sec+',';
				else
					CSV += min + ':'+sec+',';
				//*/
			}
		}

		// move to new row on excel spreadsheet
		CSV += '\r\n'
	}

	//if varaible is empty, alert invalid and return
	if (CSV == '') {        
		alert('Invalid data');
		return;
	}

	//Generate a file name
	var fileName = 'MyReport_';
	//this will remove the blank-spaces from the title and replace it with an underscore
	fileName += ReportTitle.replace(/ /g,'_');

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