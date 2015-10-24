//When DOM loaded we attach click event to button

$(function() {
	//===================================== CONSTANTS & variables =====================================

	var UPDATE_INTERVAL = 5000,				// update live results every 5 secs
			IDLE_TIMEOUT = 1200000,				// idle check after 20 minutes
			RESULTS_PER_PAGE = 25;				// results pagination

	var TABLE_VIEW = 0,
			TEAM_FINAL_VIEW = 1;

	var idArray = [],
			currentID, currentView,
			updateHandler, idleHandler, 
			sessionData, ajaxRequest,
			resultOffset = 0, currentPage = 1,
			spinner, target;

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

		// team is defined in score.html through django templating engine
		getScores(team);
		startUpdates();

	//======================================== score functions ========================================
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

	// update wrapper function
	function lastSelected() {
		update(currentID,currentView);
	}

	function getScores(team){
		getSessions(team);

		stopUpdates();
		startUpdates();
	}

	// find all heats and add to heat menu and idArray
	function getSessions(team){
		$('ul.menulist').empty();
		$.ajax({
			url: '/api/score/?team='+team ,
			dataType: 'text',
			success: function(data){
				var json = $.parseJSON(data);
				if (json.length === 0) {
					spinner.stop();
					$('#results-table').hide();
					$('#score-title').html('Live Results');
					$('#results-status').hide();
					$('p.notification.notification-default2').show();
				} else {
					$('#results-table').show();
					$('#results-status').show();
					$('p.notification.notification-default2').hide();
					var arr = [];
					for (var i=0; i < json.length; i++){
						$('ul.menulist').append('<li><a id="session-'+json[i].id+'" href="#">'+json[i].name+'</a></li>');
						arr.push(json[i].id);
					}
					idArray = arr;

					// show most recent workout
					if (!currentID)
						currentID = idArray[0];

					$('a#session-'+currentID).click();
				}
			}
		});
	}

	function update(idjson, view){
		//start ajax request
		if (ajaxRequest)
			ajaxRequest.abort();

		if (view === TABLE_VIEW)
				data = {'limit': resultOffset + RESULTS_PER_PAGE, 'offset': resultOffset};
		else if (view === TEAM_FINAL_VIEW) {
				//$('#results-table #table-canvas').empty();
				$('.notification').hide();
				$('#results-nav').show();
				drawTeam();
				return;
			}

		if (idjson == undefined || idjson === null)
			return;
		
		ajaxRequest = $.ajax({
			url: '/api/sessions/'+ idjson +'/individual_results/',
			data: data,
			dataType: 'text',		//force to handle it as text
			success: function(data) {
				data = $.parseJSON(data);

				/*
				// hardcoded for testing
				json = {
			    "id": 29, 
			    "final_score": "{\"date\": \"06.05.2015\", \"runners\": [{\"counter\": [1, 2, 3, 4], \"name\": \"Grzegorz Kalinowski\", \"interval\": \"243.952\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Sam Penzenstadler\", \"interval\": \"244.824\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Paul Escher\", \"interval\": \"244.974\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Lex Williams\", \"interval\": \"245.273\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Leland Later\", \"interval\": \"245.817\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Juan Carillo\", \"interval\": \"249.878\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Tony Zea\", \"interval\": \"259.614\"}, {\"counter\": [1, 2, 3], \"name\": \"Martin Grady\", \"interval\": \"195.147\"}, {\"counter\": [1, 2], \"name\": \"Trevor Kuehr\", \"interval\": \"120.53\"}], \"workoutID\": 29}", 
			    "name": "E13 - Elite Men"
				}
				//*/

				var results = data.results;

				// if empty, hide spinner and show notification
				if (results.length === 0) {
					spinner.stop();
					$('#notifications .notification-default').show();
					$('.results-navigate-container').hide();
					//$('.button-container').hide();
					$('#results-table').hide().empty();
				} else {
					// hide spinner and notification and show results
					spinner.stop();
					$('#notifications .notification-default').hide();
					$('.results-navigate-container').show();
					//$('.button-container').show();
					$('#results-table').empty();
					$('#results-individual').show();
					$('#results-table').append(
						'<thead>' + 
							'<tr>' +
								'<th>Name</th>' +
								'<th>Final Time</th>' +
							'</tr>' +
						'</thead>' +
						'<tbody>' +
						'</tbody>'
					);

					for (var i=0; i<results.length; i++) {
						var runner = results[i];

						var time = formatTime(Number(runner.total));

						$('#results-table tbody').append(
							'<tr>' + 
								'<td>' + runner.name + '</td>' + 
								'<td>' + time + '</td>' + 
							'</tr>'
						);
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
				}
			}
		});
	}

	function drawTeam(){
			$('.notification').hide();
			//$('#team-table-canvas').empty();
			$('#spinner').css('height', 150);
			spinner.spin(target);
			$.ajax({
				url: '/api/sessions/'+currentID+'/team_results/',
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

					//$('#team-table-canvas').empty().show();
					$('#results-team').show();
					// create table header
					if (!$.trim($('#team-table-canvas').html())) {
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
					}

					// create table rows
					for (var i=0; i<results.length; i++) {
						var team = results[i];
						var id = team.id;

					var row = $('#team-table-canvas>tbody>tr#team-'+id);
					
					if (row.length === 1) {
						
					var numDisplayedRunners = $('table#runners-team-'+id+'.table>tbody>tr').length;
					// update splits table
					//alert(team.athletes.length);
					if (team.athletes.length > numDisplayedRunners) {
						//otherwise add a single row?
						//dont need this because score will only show up with 5 runners
						//and faster runner wouldnt show up later.
						
						

						}
					}
						else{
							//  entire thing
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
						//update team score 
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
					}

					
					// stop spinner and show results
					spinner.stop();
					$('#spinner').css('height', '');
					$('#results-team').show();
					$('#download-container').show();
				}
			});
		}


	// register handlers for paginating
	$('body').on('click', 'button.prev', function(e){
		e.preventDefault();

		if (currentPage != 1) {
			resultOffset -= RESULTS_PER_PAGE;
			currentPage--;
		}

		update(currentID, currentView);
	});

	$('body').on('click', 'button.next', function(e){
		e.preventDefault();

		resultOffset += RESULTS_PER_PAGE;
		currentPage++;

		update(currentID, currentView);
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
		
	// register handler for heat menu item click
	$('body').on('click', 'ul.menulist li a', function(){
		var value = $(this).html();
		console.log( 'Index: ' + $( 'ul.menulist li a' ).index( $(this) ) );
		var indexClicked = $( 'ul.menulist li a' ).index( $(this) );

		currentID = idArray[indexClicked];

		// request for new session data
		$.ajax({
			url: '/api/sessions/'+ currentID +'/',
			dataType: 'text',
			success: function(data) {
				var json = $.parseJSON(data);

				// add heat name
				$('#score-title').html('Live Results: ' + json.name);

				spinner.spin(target);
				update(currentID, currentView);

				// update status
				if (new Date() > new Date(json.stop_time)) {
					// session is closed
					$('#results-status>span').css('color', '#d9534f');
					stopUpdates();
				} else {
					// session still active
					$('#results-status>span').css('color', '#5cb85c');
				}

				sessionData = json;
			}
		});
	});

	// Download to Excel Script
	$('#download').click(download);
});

function download(){
	var url = '/api/score/'+ currentID +'/';
	$.ajax({
		url: url,
		dataType: 'text',		//force to handle it as text
		success: function(data) {
			JSONToCSVConvertor(data, 'TRAC_Report', true); }
	});
}

function JSONToCSVConvertor(JSONData, ReportTitle, ShowLabel) {
		// data coming in must be json
		// parse through it
		var json = $.parseJSON(JSONData);  

		// initialize csv
		var CSV = '';    
		
		//Set Report title in first row or line
		CSV += ReportTitle + '\r\n\n';

		//Uncomment below when using nested json in production
		json = $.parseJSON(json.final_score);

		CSV += 'Heat Name,'+ json.name+'\r\n\n';
		CSV += 'Name \r\n'

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
					if (sec<10) {
						CSV += min + ':0'+sec+',';
					} else {
						CSV += min + ':'+sec+',';
					}
					//*/
		    }
			}
			
			//moves to new row on excel spreadsheet
			CSV += '\r\n';
		}

		//if variable is empty, alert invalid and return
		if (CSV == '') {        
			alert("Invalid data");
			return;
		}
    
    //Generate a file name
    var fileName = "MyReport_";
    //this will remove the blank-spaces from the title and replace it with an underscore
    fileName += ReportTitle.replace(/ /g,"_");   
    
    //Initialize file format you want csv or xls
    var uri = 'data:text/csv;charset=utf-8,' + escape(CSV);
    
    // Now the little tricky part.
    // you can use either>> window.open(uri);
    // but this will not work in some browsers
    // or you will not get the correct file extension    
    
    //this trick will generate a temp <a /> tag
    var link = document.createElement("a");    
    link.href = uri;
    
    //set the visibility hidden so it will not effect on your web-layout
    link.style = "visibility:hidden";
    link.download = fileName + ".csv";
    
    //this part will append the anchor tag and remove it after automatic click
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

