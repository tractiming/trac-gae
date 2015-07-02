//When DOM loaded we attach click event to button

$(function() {
	var idArray = [],
			currentID,
			updateHandler, idleHandler, 
			spinner, target;

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

		// hide all notifications
		$('.notification').hide();

		// team is defined in score.html through django templating engine
		getScores(team)
	})();

	function getScores(team){
		getSessions(team);

		// display most recent table
		lastWorkout(team);

		// refresh the view every 5 seconds to update
		clearInterval(updateHandler);
		updateHandler = setInterval(function(){lastSelected(team);}, 5000);

		// idle check after 20 minutes
		clearTimeout(idleHandler);
		idleHandler = setTimeout(
			function(){ 
				idleCheck(
					updateHandler, 
					function(){lastSelected(team);}, 
					5000, 
					1200000, 
					'http://www.trac-us.com'
				); 
			}, 1200000);
	}

	function update(idjson){
		var last_url = '/api/score/'+ idjson;

		//start ajax request
		$.ajax({
			url: last_url,
			dataType: 'text',		//force to handle it as text
			success: function(data) {
				var json = $.parseJSON(data);

				/*
				// hardcoded for testing
				json = {
			    "id": 29, 
			    "final_score": "{\"date\": \"06.05.2015\", \"runners\": [{\"counter\": [1, 2, 3, 4], \"name\": \"Grzegorz Kalinowski\", \"interval\": \"243.952\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Sam Penzenstadler\", \"interval\": \"244.824\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Paul Escher\", \"interval\": \"244.974\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Lex Williams\", \"interval\": \"245.273\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Leland Later\", \"interval\": \"245.817\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Juan Carillo\", \"interval\": \"249.878\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Tony Zea\", \"interval\": \"259.614\"}, {\"counter\": [1, 2, 3], \"name\": \"Martin Grady\", \"interval\": \"195.147\"}, {\"counter\": [1, 2], \"name\": \"Trevor Kuehr\", \"interval\": \"120.53\"}], \"workoutID\": 29}", 
			    "name": "E13 - Elite Men"
				}
				//*/

				var score = $.parseJSON(json.final_score);

				// add heat name
				$('#score-title').empty();
				$('#score-title').append('Live Results: ' + json.name);

				// if empty, hide spinner and show notification
				if (score.runners == '') {
					spinner.stop();
					$('#notifications .notification-default').show();
					//$('.button-container').hide();
					$('#results-table').hide().empty();
				} else {
					// hide spinner and notification and show results
					spinner.stop();
					$('#notifications .notification-default').hide();
					//$('.button-container').show();
					$('#results-table').empty().show();

					// style it with some bootstrap
					$('#results').addClass('col-md-6 col-md-offset-3 col-sm-8 col-sm-offset-2');

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

					for (var i=0; i < score.runners.length; i++) {
						var time = formatTime(score.runners[i].interval);

						$('#results-table tbody').append(
							'<tr>' + 
								'<td>' + score.runners[i].name + '</td>' + 
								'<td>' + time + '</td>' + 
							'</tr>'
						);
					}
				}
			}
		});
	}

	// format time in seconds to mm:ss.mil
	function formatTime(timeStr) {
		var time = Number(timeStr);
		var mins = Math.floor(time / 60);
		var secs = (time % 60).toFixed(3);
		secs = Math.floor(secs / 10) == 0 ? '0'+secs : secs;
		return mins.toString() + ':' + secs.toString();
	}
	
	function lastWorkout(team){
		$.ajax({
			url: '/api/score/?org='+team,
			dataType: 'text',
			success: function(data){
				var json = $.parseJSON(data);
				if (json.length == 0){
					spinner.stop();
					$('#results-table').hide();
					$('p.notification.notification-default2').show();
				} else {
					$('#results-table').show();
					$('p.notification.notification-default2').hide();
					var idjson = json[json.length - 1].id;
				
					update(idjson);
					currentID = idjson;
				}
			}
		});
	}
		
	function lastSelected(team){
		$.ajax({
			url: '/api/score/?org='+team,
			dataType: 'text',			//force to handle it as text
			success: function(data) {
				var json = $.parseJSON(data);
				if (json.length == 0) {
					spinner.stop();
					$('#results-table').hide();
					$('p.notification.notification-default2').show();
				} else {
					$('p.notification.notification-default2').hide();
					update(currentID);
				}
			}
		});
	}
	
	// find all heats and add to heat menu and idArray
	function getSessions(team){
		$('ul.menulist').empty();
		$.ajax({
			url: '/api/score/?org='+team,
			dataType: 'text',
			success: function(data){
				var json = $.parseJSON(data);
				if (json.length == 0) {
					spinner.stop();
					$('#results-table').hide();
					$('#score-title').html('Live Results');
					$('p.notification.notification-default2').show();
				} else {
					$('#results-table').show();
					$('p.notification.notification-default2').hide();
					var arr = [];
					for (var i=0; i < json.length; i++){
						$('ul.menulist').append('<li><a href="#">'+json[i].name+'</a></li>');
						arr.push(json[i].id);
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

		// set new heat id and update table contents
		spinner.spin(target);
		currentID = idArray[indexClicked];
		update(currentID);
	});

	// Download to Excel Script
	$('#download').click(download);
});

function download(){
	var url = '/api/score/'+ currentID;
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