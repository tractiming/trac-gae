if (sessionStorage.usertype == 'athlete'){
	location.href = '/home.html';
}

$(function() {
	var mostInstance= 0,
			sessionFirst = 1,
			sessionLast = 11;

	var opts = {
		lines: 13, 							// The number of lines to draw
		length: 28, 						// The length of each line
		width: 14, 							// The line thickness
		radius: 42, 						// The radius of the inner circle
		scale: 0.3, 						// Scales overall size of the Spinner
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
	var spinner = new Spinner(opts);
	
	loadworkouts();
	
	function loadworkouts() {
		$('#results').empty();
		spinner.spin(target);
		$.ajax({
			url: '/api/session_Pag/',
			headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
			data: {
				i1: sessionFirst,
				i2: sessionLast,
			},
			dataType: 'text',
			success: function(data) {
				var json = $.parseJSON(data);
				json = json.reverse();

				if (json == '') {
					$(".outer").hide();
					$(".modal-animate").hide();
					$('#results').empty();
					$('button#next').hide();
					$('button#prev').show();
					$("div.notification.notification-default").show();
				} else {
				// show name and date, dont show message, but show button
					$(".outer").show();
					$("div.notification.notification-default").hide();
					$('#results').append(
						'<table id="results-table" class="table table-striped table-hover">' +
							'<thead>' +
								'<tr>' +
									'<th class="hidden-xs hidden-sm hidden-md hidden-lg">id</th>' +
									'<th>Workout Name</th>' +
									'<th>Start Date</th>' +
									'<th class="hidden-xs hidden-sm">End Date</th>' +
									'<th class="hidden-xs hidden-sm">Distance</th>' +
									'<th class="hidden-xs hidden-sm">Track</th>' +
									'<th>Filtered</th>' +
									'<th class="hidden-xs hidden-sm">Private</th>' +
								'</tr>' +
							'</thead>' +
							'<tbody>' +
							'</tbody>' +
						'</table>'
					);

					$('#results').addClass('col-md-6 col-md-offset-0 colr-sm-8 col-sm-offset-0');
					var maximum = 0;
					for (var ii=0; ii < json.length;ii++){
						if (ii > maximum){
							maximum = ii;
						}

						id = json[ii].id;
						name = json[ii].name;
						distance = json[ii].interval_distance;
						track = json[ii].track_size;
						filter= json[ii].filter_choice;
						privateselect = json [ii].private;
						var sTS = UTC2local(json[ii].start_time);
						sTS = sTS.substring(0, 25);
						var sTE = UTC2local(json[ii].stop_time);
						sTE = sTE.substring(0,25);

						$('#results tbody').append(
							'<tr>'+
								'<td class="hidden-xs hidden-sm hidden-md hidden-lg">' + id + '</td>' +
								'<td>'+name+'</td>'+
								'<td>'+sTS+'</td>'+
								'<td class="hidden-xs hidden-sm">'+sTE+'</td>'+
								'<td class="hidden-xs hidden-sm">'+distance+'</td>'+
								'<td class="hidden-xs hidden-sm">'+track+'</td>'+
								'<td>'+filter+'</td>'+
								'<td class="hidden-xs hidden-sm">'+privateselect+'</td>'+
							'</tr>'
						);
					}

					if (maximum < 8){
						$('button#next').hide();
					} else {
						$('button#next').show();
					}

					if (sessionFirst == 1){
						$('button#prev').hide();
					} else {
						$('button#prev').show();
					}
				}
			}
		});
		spinner.stop();
	}
	  
	$("body").on('click', 'tr',function(){
		$('#myModal').modal('toggle');
		var value = $(this).html();
		$("button#delete").show();
		$("input#update").show();
		$("div.button-container-two").show();
		$("input#create").show();
		$("p#idnumber").show();
		$("input#save").hide();
		$(value).each(function(index){
			if (index ==0) {
				var input =$('input#idnumber');
				input.val($(this).html() );
			} else if (index ==1) {
				var input =$('input#title');
				input.val($(this).html() );
			} else if (index ==2) {
				var input =$('input#start_date');
				var format = new Date($(this).html());
				format = format.toISOString();
				format = localISOString(format);
				format = format.replace(/T/g,' ');
				format = format.substring(0,19);
				format = format.replace(/;/g, ':');
				input.val(format);
			} else if (index ==3) {
				var input =$('input#end_date');
				var format = new Date($(this).html());
				format = format.toISOString();
				format = localISOString(format);
				format = format.replace(/T/g,' ');
				format = format.substring(0,19);
				format = format.replace(/;/g, ':');
				input.val(format);
			} else if (index ==4) {
				var input =$('input#distance');
				input.val($(this).html() );
			} else if (index ==5) {
				var input =$('input#size');
				input.val($(this).html() );
			} else if (index ==6) {
				var input =$('select#filter');
				input.val($(this).html() );
			} else if (index ==7) {
				var input =$('select#private');
				input.val($(this).html() );
			}
		});
	});
	
	$("body").on('click', 'button#create', function(e){
		e.preventDefault();
		$("#myform")[0].reset();
		var value = $(this).html();
		$("button#delete").hide();
		$("input#update").hide();
		$("input#save").show();
		$("p#idnumber").hide();
		//$("input#create").hide();
	});

	// on submit prevent default of form and show spinner
	$('input#save').click( function(e){
		e.preventDefault();
		$(".modal-animate").show();
		var form = $(this);

		//validate that form is correclty filled out

		//if valid perform ajax request
		var title=$('input[id=title]').val();
		var start_date=$('input[id=start_date]').val();
		var end_date=$('input[id=end_date]').val();
		var distance=$('input[id=distance]').val();
		var size=$('input[id=size]').val();
		var filter=$('#filter option:selected').val();
		var privateselect=$('#private option:selected').val();
		var sT = local2UTC(start_date);
		var eT = local2UTC(end_date);

		$.ajax({
			type: "POST",
			dataType:'json',
			url: "/api/time_create/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			data: {
				id: 0,
				name: title,
				start_time: sT,
				stop_time: eT,
				rest_time: '0',
				track_size: size,
				interval_distance: distance,
				interval_number:'0',
				filter_choice:filter,
				private:privateselect,
			},
			success: function(data) {
				//hide spinner, success modal, and reset form
				$(".modal-animate").hide();
				$("div.notification.notification-critical").hide();
				$("div.notification.update-success").hide();
				$("div.notification.delete-success").hide();
				$("div.notification.notification-success").show();
				$("#myform")[0].reset();
				$(".outer").show();
				$("div.notification.notification-default").hide();
				loadworkouts();
			},
			error: function(xhr, errmsg, err) {
				//hide spinner, show error modal
				$(".modal-animate").hide();
				$("div.notification.notification-success").hide();
				$("div.notification.update-success").hide();
				$("div.notification.delete-success").hide();
				$("div.notification.notification-critical").show();
			}
		});
	});

	$("body").off('click', 'button#delete');
	$("body").on('click', 'button#delete', function(f){
	//alert($(this).html());
		f.preventDefault();
		$("div.notification.notification-warning").show();
		$("div.notification.notification-critical").hide();
		$("div.notification.notification-critical").hide();
		$("div.notification.notification-success").hide();
		$("div.notification.update-success").hide();
	});

	$("body").on('click', 'button#warning-yes', function(event){
		var value = $(this).html();
		$(".modal-animate").show();

		var id=$('input[id=idnumber]').val();
		//alert(id);
		//alert(filter);

		$.ajax({
			type: "DELETE",
			dataType:'json',
			url: "/api/time_create/"+id,
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			success: function(data) {
				//hide spinner, success modal, and reset form
				$(".modal-animate").hide();
				$("div.notification.notification-critical").hide();
				$("div.notification.notification-success").hide();
				$("div.notification.update-success").hide();
				$("div.notification.delete-success").show();
				$("div.notification.notification-warning").hide();
				$("#myform")[0].reset();
				$("button#delete").hide();
				$("input#update").hide();
				$("input#save").show();
				$("p#idnumber").hide();
				//$("input#create").hide();
				$("#results").empty();
				loadworkouts();
			},
			error: function(xhr, errmsg, err) {
				//hide spinner, show error modal
				$(".modal-animate").hide();
				$("div.notification.notification-success").hide();
				$("div.notification.notification-warning").hide();
				$("div.notification.update-success").hide();
				$("div.notification.delete-success").hide();
				$("div.notification.notification-critical").show();
			}
		});
	});

	$("button#warning-no").click(function(event){
		$(".modal-animate").hide();
		$("div.notification.notification-success").hide();
		$("div.notification.notification-warning").hide();
	});

	$("body").on('hidden.bs.modal', '#notificationModal', function(){
		$("div.notification.delete-success").hide();
		$("div.notification.notification-warning").hide();
	});

	$("body").on('click', 'button#prev',function(f){
		if(sessionFirst != 1){
			sessionFirst -= 10;
			sessionLast -= 10;
		}

		loadworkouts();
	});

	$("body").on('click', 'button#next',function(f){
		sessionFirst += 10;
		sessionLast += 10;
		loadworkouts();
	});

	$("body").on('click', 'input#update',function(f){
		//alert($(this).html());
		f.preventDefault();
		$(".modal-animate").show();
		var id=$('input[id=idnumber]').val();
		var title=$('input[id=title]').val();
		var start_date=$('input[id=start_date]').val();
		var end_date=$('input[id=end_date]').val();
		var distance=$('input[id=distance]').val();
		var size=$('input[id=size]').val();
		var filter=$('#filter option:selected').val();
		var privateselect=$('#private option:selected').val();
		var sT = local2UTC(start_date);
		var eT = local2UTC(end_date);

		$.ajax({
			type: "POST",
			dataType:'json',
			url: "/api/sessions/",
			headers: {Authorization: "Bearer " + sessionStorage.access_token},
			data: {
				id: id,
				name: title,
				start_time: sT,
				stop_time: eT,
				rest_time: '0',
				track_size: size,
				interval_distance: distance,
				interval_number:'0',
				filter_choice:filter,
				private:privateselect,
			},
			success: function(data) {
				//hide spinner, success modal, and reset form
				$(".modal-animate").hide();
				$("div.notification.notification-critical").hide();
				$("div.notification.notification-success").hide();
				$("div.notification.delete-success").hide();
				$("div.notification.update-success").show();
				$("#myform")[0].reset();
				$("button#delete").hide();
				$("input#update").hide();
				$("input#save").show();
				$("p#idnumber").hide();
				//$("input#create").hide();
				loadworkouts();
			},
			error: function(xhr, errmsg, err) {
				//hide spinner, show error modal
				$(".modal-animate").hide();
				$("div.notification.notification-success").hide();
				$("div.notification.notification-warning").hide();
				$("div.notification.update-success").hide();
				$("div.notification.delete-success").hide();
				$("div.notification.notification-critical").show();
			}
		});
	});
});