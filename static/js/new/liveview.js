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

				json = $.parseJSON(json.results);

				//if empty show notification, hide spinner, and show button
				if (json.runners == "") {
					$(".modal-animate").hide();
					$("h6.notification.notification-default").show();
					$("input#submit.gen_btn").show();
					$('#results').empty();
				} else {
					//hide spinner, show button, show results
					$("div.inner").show();
					$(".modal-animate").hide();
					$("h6.notification.notification-default").hide();
					$("input#submit.gen_btn").show();
					var longest = 0;
					var importantRow;

					for (var ii = 0; ii < json.runners.length; ii++) {
						for (var jj = 0; jj < json.runners[ii].interval.length; jj++){
							if (jj == 0) {
								//initilize temporary variable
								var tempLength = json.runners[ii].interval[jj].length;
							} else {
								tempLength = tempLength + json.runners[ii].interval[jj].length;
							}
						}
						if (longest < tempLength) {
							longest = tempLength;
							importantRow = ii;
						}
					}

					$('#results').empty();
					for (var i=0; i < json.runners.length; i++) {
						//print names and enter name array
						var name = json.runners[i].name;

						if (i==0) {
							$('#results').append('<tr><td>Name</td></tr>');
							$('#results').append('<tr class="odd"><td>'+name+'</td></tr>');
						} else if((i)%2 ==0) {
							$('#results').append('<tr class="odd"><td>'+name+'</td></tr>');
						} else {
							$('#results').append('<tr><td>'+name+'</td></tr>');
						}

						var finaltime = 0;

						for (var j=0; j < json.runners[i].interval.length; j++) {
							//iterate over interval to get to nested time arrays
							var interval = json.runners[i].interval[j];
							//$('#results').append( "Interval Subset: ")

							for (var k=0; k < json.runners[i].interval[j].length; k++) {
								//interate over subarrays and pull out each individually and print
								var subinterval = json.runners[i].interval[j][k];
								var min = Math.floor(subinterval/60);
								var sec = (subinterval-(min*60));
								// $('#results').append('<td>');
								//This if statements adds the preceding 0 to any second less than 10
								$('#results tr:last').append('<td>'+ subinterval +'</td>');
								/*
								if (sec<10) {
									$('#results tr:last').append('<td>'+ min + ':0'+ sec +'</td>');
								} else {
									$('#results tr:last').append('<td>'+ min + ':'+ sec +'</td>');
								}
								//*/
								finaltime = finaltime + subinterval;
								if (i==importantRow) {
									//Puts the word 'split #' on table
									$('#results tr:first').append('<td>' + 'Split' + '</td>');
								}
							}
						}
			  		
			  		/*
						//to implement total time-- not necessary for this moment
						var minfinal = Math.floor(finaltime/60);
						var secfinal = (finaltime-(minfinal*60));

						if (secfinal<10) {
							$('#results tr:last').append( minfinal + ':0'+ secfinal );
						} else {
							$('#results tr:last').append( minfinal + ':'+ secfinal);
						}
						if (i==0) {
							//adds word final time to table header
							$('#results tr:first').append('<td>Final Time</td>');
						}
						//*/
					}
				}
			}
		});
	}

	function lastWorkout(){
		$.ajax({
			url: "/api/sessions/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			dataType: "text",			//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
				//alert(json.length);
				if (json.length==0){ 
					$("h6.notification.notification-default2").show();
					$(".modal-animate").hide();
				} else {
					$("h6.notification.notification-default2").hide();
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
			url: "/api/sessions/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			dataType: "text",			//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
				//alert(json.length);
				if (json.length==0){ 
					$("h6.notification.notification-default2").show();
					$(".modal-animate").hide();
				} else {
					$("h6.notification.notification-default2").hide();
					update(selectedID);
				}
			}
		});
	}
		
	function findScores(){
		$.ajax({
			url: "/api/sessions/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			dataType: "text",			//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
				//alert(json.length);
				if (json.length==0){ 
					$("h6.notification.notification-default2").show();
					$(".modal-animate").hide();
				} else {
					$("h6.notification.notification-default2").hide();
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
		
	$("body").on('click', 'ul.menulist li a',function(){
		//alert($(this).html());
		var value = $(this).html();
		console.log( "Index: " + $( "ul.menulist li a" ).index( $(this) ) );
		var indexClicked= $( "ul.menulist li a" ).index( $(this) );
		//alert(idArray);
		//alert(idArray[indexClicked]);
		selectedID = idArray[indexClicked];
		update(idArray[indexClicked]);
	});
	
	//Download to Excel Script
	$('#submit').click(function(){
		$.ajax({
			url: "/api/sessions/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			dataType: "text",			//force to handle it as text
			success: function(data){
				urlfn(selectedID);
				return selectedID;
			}
		});
	});
});

	var urlfn = function(idjson){
		var last_url = "/api/sessions/"+ idjson;
		//alert(last_url);
		$.ajax({
			url: last_url,
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			dataType: "text",			//force to handle it as text
			success: function(data) {
				JSONToCSVConvertor(data, "TRAC_Report", true);
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
   //alert(CSV);
   CSV += 'Name \r\n'
   //Uncomment below when using nested json in production
   json = $.parseJSON(json.results);
   
	      //iterate into name array
	       for (var i=0; i < json.runners.length; i++) {
		  //print names and enter name array
		  var name = json.runners[i].name; 
		    CSV +=name+',';
		  
		//alert(CSV);
   
   
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
			      //This if statements adds the preceding 0 to any second less than 10
			      //if (sec<10) {
				//CSV += min + ':0'+sec+',';
			      //}
			      //else
			      //{
			      //CSV += min + ':'+sec+',';
			      //}
			      
			    }
			  }
			  //moves to new row on excel spreadsheet
			  CSV += '\r\n'
	       }
   
   //if varaible is empty, alert invalid and return
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