var idArray=[];
var selectedID;
//When DOM loaded we attach click event to button
$(function() {

	var updateHandler, spinner;

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
		var target = document.getElementById('spinner');
		spinner = new Spinner(opts).spin(target);

		// hide all notifications
		$('.notification').hide();
		$('#download-container').hide();

		findScores();

		// display most recent table
		lastWorkout();

		// refresh the view every 5 seconds to update
		updateHandler = setInterval(lastSelected, 5000);

		// idle check after 20 minutes
		setTimeout(function(){ idleCheck(updateHandler, lastSelected, 5000, 1200000, 'http://www.trac-us.com'); }, 1200000);
	})();

	function update(idjson) {
		var last_url = '/api/sessions/'+ idjson;
		
		//start ajax request
		$.ajax({
			url: last_url,
			headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
			dataType: 'text',			//force to handle it as text
			success: function(data) {
				var json = $.parseJSON(data);

				//*
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
					"results": "{\"date\": \"06.05.2015\", \"runners\": [{\"counter\": [1, 2, 3], \"name\": \"Max Denning\", \"interval\": [[\"64.83\"], [\"65.05\"], [\"140.015\"]]}, {\"counter\": [1, 2, 3, 4], \"name\": \"Michael Ronzone\", \"interval\": [[\"65.477\"], [\"69.653\"], [\"79.168\"], [\"79.696\"]]}], \"workoutID\": 24}", 
					"athletes": "[\"MaxDenning\", \"MichaelRonzone\"]", 
					"start_button_time": "2015-06-06T01:29:29Z", 
					"private": true
				};
				//*/

				var results = $.parseJSON(json.results);

				// add heat name
				$('#results-title').empty();
				$('#results-title').append('Live Results: ' + json.name);

				// if empty, hide spinner and show notification
				if (results.runners == '') {
					spinner.stop();
					$('#notifications .notification-default').show();
					$('#download-container').hide();
					$('#results-table').hide().empty();
				} else {
					// hide spinner and notification and show results
					spinner.stop();
					$('#notifications .notification-default').hide();
					$('#download-container').show();
					$('#results-table').empty().show();

					// style it with some bootstrap
					$('#results').addClass('col-md-6 col-md-offset-3 col-sm-8 col-sm-offset-2');

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

					for (var i=0; i < results.runners.length; i++) {
						var interval = results.runners[i].interval;

						$('#results-table>tbody').append(
							'<tr id="results'+i+'" class="accordion-toggle" data-toggle="collapse" data-parent="#results-table" data-target="#collapse'+i+'" aria-expanded="false" aria-controls="collapse'+i+'">' + 
								'<td>' + results.runners[i].name + '</td>' + 
								'<td>' + interval[interval.length-1][0] + '</td>' + 
								'<td></td>' + 
							'</tr>' + 
							'<tr></tr>'	+		// for correct stripes 
							'<tr class="splits">' +
								'<td colspan="3">' +
									'<div id="collapse'+i+'" class="accordion-body collapse" aria-labelledby="results'+i+'">' + 
										'<table class="table" style="text-align:center; background-color:transparent">' +
											/*'<thead>' + 
												'<tr>' +
													'<th>Split</th>' +
													'<th>Time</th>' +
												'</tr>' +
											'</thead>' + */
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

							// add splits to subtable
							$('#collapse'+i+' tbody').append(
								'<tr>' + 
									'<td>' + (j+1) + '</td>' + 
									'<td>' + interval[j][0] + '</td>' + 
								'</tr>'
							);

							// now calculate total time
							total += Number(interval[j][0]);
						}

						// display total time
						total = formatTime(String(total));
						$('#results-table>tbody #results'+i+'>td').last().html(total);
						//*/
					}
				}
			}
		});
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
					update(idjson);
					selectedID = idjson;
					//alert(selectedID);
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
					update(selectedID);
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
					var Array = [];
					for (var ii=0; ii < json.length; ii++){
						$('#linkedlist').append('<tr><td>'+json[ii].name+'</td></tr>');
						$('ul.menulist').append('<li><a href="#">'+json[ii].name+'</a></li>');
						Array.push(json[ii].id);
					}
					idArray = Array;
				}
			}
		});
	}

	// attach handler for heat menu item click
	$('body').on('click', 'ul.menulist li a', function(){
		var value = $(this).html();
		console.log( 'Index: ' + $( 'ul.menulist li a' ).index( $(this) ) );
		var indexClicked = $( 'ul.menulist li a' ).index( $(this) );

		// set new heat id and update table contents
		spinner.spin(target);
		selectedID = idArray[indexClicked];
		update(selectedID);
	});
	
	//Download to Excel Script
	$('#download').click(function(){
		$.ajax({
			url: '/api/sessions/',
			headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
			dataType: 'text',			//force to handle it as text
			success: function(data){
				urlfn(selectedID);
				return selectedID;
			}
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