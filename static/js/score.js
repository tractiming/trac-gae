var idArray = [];
var selectedID;

//When DOM loaded we attach click event to button
$(document).ready(function() {
	
	function update(idjson){
		var last_url = '/api/score/'+ idjson;
    
		//start ajax request
		$.ajax({
			url: last_url,
			dataType: 'text',		//force to handle it as text
			success: function(data) {
				var json = $.parseJSON(data);

				// hardcoded for testing
				json = {
			    "id": 29, 
			    "final_score": "{\"date\": \"06.05.2015\", \"runners\": [{\"counter\": [1, 2, 3, 4], \"name\": \"Grzegorz Kalinowski\", \"interval\": \"243.952\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Sam Penzenstadler\", \"interval\": \"244.824\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Paul Escher\", \"interval\": \"244.974\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Lex Williams\", \"interval\": \"245.273\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Leland Later\", \"interval\": \"245.817\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Juan Carillo\", \"interval\": \"249.878\"}, {\"counter\": [1, 2, 3, 4], \"name\": \"Tony Zea\", \"interval\": \"259.614\"}, {\"counter\": [1, 2, 3], \"name\": \"Martin Grady\", \"interval\": \"195.147\"}, {\"counter\": [1, 2], \"name\": \"Trevor Kuehr\", \"interval\": \"120.53\"}], \"workoutID\": 29}", 
			    "name": "E13 - Elite Men"
				}

				var score = $.parseJSON(json.final_score);
				
				score.runners = '';

				// add heat name
				$('#score-title').empty();
				$('#score-title').append('Live Results: ' + json.name);

				// if empty, show notification
				if (score.runners == '') {
					$('#notifications .notification-default').show();
					$('.button-container').hide();
					$('#results').empty().hide();
				} else {
					// hide notification and show results
					$('#notifications .notification-default').hide();
					$('.button-container').show();
					$('#results').empty();

					// table template
					$('#results').append(
						'<table id="results-table" class="table table-striped table-hover tablesorter">' + 
							'<thead>' + 
								'<tr>' + 
									'<th>Name</th>' + 
									'<th>Final Time</th>' + 
								'</tr>' + 
							'</thead>' +
			  			'<tbody>' +
				  		'</tbody>' +
						'</table>'
					);

					// style it with some bootstrap
					$('#results').addClass('col-md-6 col-md-offset-3');

					// add tablesorter
					//$('#results-table').tablesorter();

					for (var i=0; i < score.runners.length; i++) {
						var time = formatTime(score.runners[i].interval);

						$('#results tbody').append(
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
	
	function lastWorkout(){
		$.ajax({
			url: '/api/score/',
			dataType: 'text',			//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
			
				if (json.length==0){ 
					$("h6.notification.notification-default2").show();
					$(".modal-animate").hide();
				} else {
					$("h6.notification.notification-default2").hide();
					var idjson = json[json.length - 1].id;
				
					update(idjson);
					selectedID = idjson;
				}
			}
		});
	}
		
	function lastSelected(){
		$.ajax({
			url: "/api/score/",
			dataType: "text",			//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
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
			url: "/api/score/",
			dataType: "text",		//force to handle it as text
			success: function(data){
				var json = $.parseJSON(data);
				if (json.length==0){ 
					$("h6.notification.notification-default2").show();
					$(".modal-animate").hide();
				} else {
					$("h6.notification.notification-default2").hide();
					var arr = [];
					for (var i=0; i < json.length; i++){
						$('#linkedlist').append('<tr><td>'+json[i].name+'</td></tr>');
						$('ul.menulist').append('<li><a href="#">'+json[i].name+'</a></li>');
						arr.push(json[i].id);
					}
					idArray = arr;
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
	
	findScores();
		//refresh the view every 5 seconds to update
	    lastWorkout();
	   setInterval(lastSelected ,5000);


//Download to Excel Script

    $('#submit').click(function(){
        $.ajax({
                    url: "/api/score/" + selectedID,
		    
                    //force to handle it as text
                    dataType: "text",
                    success: function(data){
		      var json = $.parseJSON(data);
			//alert(json.length);
			//alert(selectedID)
			//alert(idjson);
			urlfn(selectedID);
			return selectedID;
		    }
		    
	    });
    });
});
	

  
  var urlfn = function(){
    var last_url = "/api/score/"+ selectedID;
    //alert(last_url);
     $.ajax({
                    url: last_url,
		    
                    //force to handle it as text
                    dataType: "text",
                    success: function(data) {
        
        JSONToCSVConvertor(data, "TRAC_Report", true);}});
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



   //Uncomment below when using nested json in production
   json = $.parseJSON(json.final_score);
   
      CSV += 'Heat Name,'+ json.name+'\r\n\n';
      CSV += 'Name \r\n'
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