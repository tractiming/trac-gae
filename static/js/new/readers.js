if (sessionStorage.usertype == 'athlete'){
	location.href='/home.html';
}

$(function() {
	var idArray = [],
			currentID,
			updateHandler, 
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

		// get all the readers
		getReaders();

		// display most recent table
		//lastWorkout();

		// refresh the view every 5 seconds to update
		//updateHandler = setInterval(lastSelected, 5000);

		// idle check after 20 minutes
		//setTimeout(function(){ idleCheck(updateHandler, lastSelected, 5000, 1200000, 'http://www.trac-us.com'); }, 1200000);
	})();

	//function to load reader info
	function getReaders(){
		$('#results-table').empty();
		$.ajax({
			url: '/api/readers/',
			headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
			dataType: 'text',
			success: function(data) {
				var json = $.parseJSON(data);
				if (json == '') {
					$('.notifications.no-results').show();
					spinner.stop();
				} else {
					$('.notification').hide();
					spinner.stop();

					// add table head if empty
					if (!$.trim($('#results-table').html())) {
						$('#results-table').append(
							'<thead>' + 
								'<tr>' +
									'<th style="text-align:center;">Name</th>' +
									'<th style="text-align:center;">ID Number</th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>'
						);
					}

					// now add readers to table
					for (var i=0; i<json.length; i++) {
						$('#results-table tbody').append(
							'<tr id="'+json[i].id+'" data-toggle="modal" data-target="#edit-modal">' +
								'<td>' + json[i].name + '</td>' +
								'<td>' + json[i].id_str + '</td>' +
							'</tr>'
						);
					}

					$('#results-table tbody tr').click(function(e) {
						e.preventDefault();
						$('#edit-modal #edit-form input#id').val(this.id);
						$('#edit-modal #edit-form input#name').val($(this).find('td')[0].innerText);
						$('#edit-modal #edit-form input#id-str').val($(this).find('td')[1].innerText);
					});
				}
			}
		});
	}

	$('#edit-submit').on('click', function(e) {
		e.preventDefault();
		console.log($('input#id').val());
	});
});





$(document).ready(function() {
	$(".modal-animate").show();
		loadreader();
        $("#myform").on('click','#submit', function(e){
            e.preventDefault();
	    $(".modal-animate").show();


	            // var title=$('input[id=title]').val();
	           var name=$('input[id=readername]').val();
		      var idstr=$('input[id=readernum]').val();
		    

	      $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/readers/",
	   headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
               name: name,
               id_str:idstr,
               
           },
           // Login was successful.
           success: function(data) {
			  
			      
		    $(".modal-animate").hide();
		    $("h6.notification.notification-critical").hide();
		    $("h6.notification.notification-success").show();
		    $("#myform")[0].reset();
			   loadreader();
           },

           // create athlete failed.
           error: function(xhr, errmsg, err) {
	    $(".modal-animate").hide();
	    $("h6.notification.notification-success").hide();
               $("h6.notification.notification-critical").show();
           }
           
      });
               
            
        });
    });



$("body").on('click', 'tr',function(){
	//alert($(this).html());
	var value = $(this).html();
	$("input#delete").show();
	$("input#update").show();
	$("div.button-container-two").show();
	$("input#create").show();
	$("p#idnumber").show();
	$("input#submit").hide();
	$(value).each(function(index){
		//alert( $(this).html() );
		console.log( index+ ":"+ $(this).html());
		if (index ==0)
		{
			var input =$('input#idnumber');
			input.val($(this).html() );
		}
		else if (index ==1)
		{
			var input =$('input#readername');
			input.val($(this).html() );
			}
		else if (index ==2)
		{
			var input =$('input#readernum');
			input.val($(this).html() );
			}

	});
	
	

	
	
	});
	
	$("body").on('click', 'input#create',function(e){
	//alert($(this).html());
	  e.preventDefault();
	  $("#myform")[0].reset();
	var value = $(this).html();
	$("input#delete").hide();
	$("input#update").hide();
	$("input#submit").show();
	$("p#idnumber").hide();
	$("input#create").hide();

	});



	$("body").on('click', 'input#delete',function(f){
	//alert($(this).html());
	  f.preventDefault();
	  $("h6.notification.notification-warning").show();
	  $("h6.notification.notification-critical").hide();
	  $("h6.notification.delete-success").hide();
	  		    $("h6.notification.notification-critical").hide();
		    $("h6.notification.notification-success").hide();
		     $("h6.notification.update-success").hide();
	  
	   $("body").on('click','button',function(event){
	console.log("On:", event.target);
	var value = $(this).html();
	if (value == 'Yes'){ $(".modal-animate").show();
	  
	 var id=$('input[id=idnumber]').val();
	//alert(id);
	
		//alert(filter);
	      $.ajax({
           type: "DELETE",
           dataType:'json',
           url: "/api/readers/"+id,
	   headers: {Authorization: "Bearer " + sessionStorage.access_token},
         
           // Login was successful.
           success: function(data) {
		    //hide spinner, success modal, and reset form
		    $(".modal-animate").hide();
		    $("h6.notification.notification-critical").hide();
		    $("h6.notification.notification-success").hide();
		     $("h6.notification.update-success").hide();
		    $("h6.notification.delete-success").show();
		     $("h6.notification.notification-warning").hide();
		    $("#myform")[0].reset();
		    	$("input#delete").hide();
	$("input#update").hide();
	$("input#submit").show();
	$("p#idnumber").hide();
	$("input#create").hide();
		    loadreader();
                   
           },

           // Login request failed.
           error: function(xhr, errmsg, err) {
	    //hide spinner, show error modal
	    $(".modal-animate").hide();
	    $("h6.notification.notification-success").hide();
	     $("h6.notification.notification-warning").hide();
	      $("h6.notification.update-success").hide();
		    $("h6.notification.delete-success").hide();
               $("h6.notification.notification-critical").show();
           }
           
      });
      }
	else if(value =='Cancel'){
		$(".modal-animate").hide();
	    $("h6.notification.notification-success").hide();
	    $("h6.notification.notification-warning").hide();
              
		}
	
	 });
	  
	  
	
	});
	
	
		$("body").on('click', 'input#update',function(f){
	//alert($(this).html());
	  f.preventDefault();
	   $(".modal-animate").show();
	 var id=$('input[id=idnumber]').val();
	           var name=$('input[id=readername]').val();
		      var idstr=$('input[id=readernum]').val();

	
		//alert(filter);
	      $.ajax({
           type: "PUT",
           dataType:'json',
           url: "/api/readers/"+id,
	   headers: {Authorization: "Bearer " + sessionStorage.access_token},
	   data: {
               name: name,
               id_str:idstr,
               
           },

           // Login was successful.
           success: function(data) {
		    //hide spinner, success modal, and reset form
		    $(".modal-animate").hide();
		    $("h6.notification.notification-critical").hide();
		    $("h6.notification.notification-success").hide();
		    $("h6.notification.delete-success").hide();
		    $("h6.notification.update-success").show();
		    $("#myform")[0].reset();
		    	$("input#delete").hide();
	$("input#update").hide();
	$("input#submit").show();
	$("p#idnumber").hide();
	$("input#create").hide();
		    loadreader();
                   
           },

           // Login request failed.
           error: function(xhr, errmsg, err) {
	    //hide spinner, show error modal
	    $(".modal-animate").hide();
	    $("h6.notification.notification-success").hide();
	     $("h6.notification.notification-warning").hide();
	      $("h6.notification.update-success").hide();
		    $("h6.notification.delete-success").hide();
               $("h6.notification.notification-critical").show();
           }
           
      });
	
	});
	
