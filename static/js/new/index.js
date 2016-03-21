$(function() {

	//=================================== datepicker configuration ====================================
	var datepickerOptions = {
		todayHighlight: true,
		todayBtn: true,
		datesDisabled:[new Date()],
		startDate: '+0d',
	};
	$('input#start-date').datepicker(datepickerOptions);
	$('input#end-date').datepicker(datepickerOptions);


	var tag_type=1, num_tags=5000, systems=3, startTime = [9,0], startDate, startAMPM, shipping=0,email;

	$("#tags").keypress(function (e) {
	//if the letter is not digit then display error and don't type anything
	if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
	return false;
	}
	});


	//Text Change listeners for dynamic pricing
	$("input[name=tag_type]").on('change', function(){
	  tag_type = $("input[name=tag_type]:checked").val();
	  changePricing(tag_type,num_tags,systems,shipping);
	})

	$("#tags").on('input', function(){
	  num_tags = $('#tags').val();
	  changePricing(tag_type,num_tags,systems,shipping);
	});

	$("#systems").on('input', function(){
	  systems = $('#systems').val();
	  changePricing(tag_type,num_tags,systems,shipping);
	});

	$("#email").on('input', function(){
	  email = $('#email').val();
	 
	});

	function changePricing(tag_type,num_tags,systems,diff){
	  price = (tag_type * num_tags) + (systems * 350) + (systems * diff) + (diff/3);

	  $('#pricing').text('Estimated Price: $' + price.toLocaleString()+'.00');

	};


	  // Close Checkout on page navigation
	  $(window).on('popstate', function() {
	  //handler.close();
	  });


	$("input[id=start-date]").on('change', function(){
	startDate = $('input[id=start-date]').val().trim().split(/[\/-]/),
						startTime = $('input[id=start-time]').val().trim().split(':').map(Number),
						startAMPM = $('select#start-am-pm').val();

	console.log(startTime);
	// create start date object
	var startDateTime = new Date();
	startDateTime.setFullYear(startDate[2]);
	startDateTime.setMonth(startDate[0]-1);
	startDateTime.setDate(startDate[1]);

	if ((startAMPM == 'PM' ) && (startTime[0] < 12))
		startDateTime.setHours(startTime[0]+12);
	else if ((startAMPM == 'AM') && (startTime[0] == 12))
		startDateTime.setHours(startTime[0]-12);
	else
		startDateTime.setHours(startTime[0]);

	startDateTime.setMinutes(startTime[1]);

	if (startTime.length > 2)
		startDateTime.setSeconds(startTime[2]);
	else
		startDateTime.setSeconds(0);

	var diff = Math.abs(new Date() - startDateTime);
	if (diff < 86400000)
		shipping = 300;
	else if (diff < 172800000)
		shipping = 150;
	else if (diff < 259200000) 
		shipping = 30;
	else
		shipping = 0;

	changePricing(tag_type,num_tags,systems,shipping);
});


		$('body').on('click', 'button#quote', function(e){
			e.preventDefault();
				//validate that form is correctly filled out
				var form = $('#session-form');
				form.parsley().validate();

				if (!form.parsley().isValid())
					return;

				// reset parsley styling
				form.parsley().reset();

				// hide button and show spinner
				//$('.session-form-buttons').hide();
				//target = $('#spinner-form');
				//target.css('height', 50);
				//spinner.spin(target[0]);

				var name = $('input[id=title]').val();
				var email = $('input[id=email]').val();
				var stripePrice = price *100;

			  // .open({
			  // 	email: email,
			  //   name: 'TRAC',
			  //   description: 'TRAC Timing',
			  //   amount: stripePrice,
			  //   shippingAddress:true,
			  // });
			  // e.preventDefahandlerult();

				// get start date and time
				var startDate = $('input[id=start-date]').val().trim().split(/[\/-]/),
						startTime = $('input[id=start-time]').val().trim().split(':').map(Number),
						startAMPM = $('select#start-am-pm').val();
				
				// create start date object
				var startDateTime = new Date();
				startDateTime.setFullYear(startDate[2]);
				startDateTime.setMonth(startDate[0]-1);
				startDateTime.setDate(startDate[1]);

				if ((startAMPM == 'PM' ) && (startTime[0] < 12))
					startDateTime.setHours(startTime[0]+12);
				else if ((startAMPM == 'AM') && (startTime[0] == 12))
					startDateTime.setHours(startTime[0]-12);
				else
					startDateTime.setHours(startTime[0]);

				startDateTime.setMinutes(startTime[1]);

				if (startTime.length > 2)
					startDateTime.setSeconds(startTime[2]);
				else
					startDateTime.setSeconds(0);

				var tag_type = $("input[name=tag_type]:checked").val();
				var num_tags = $('input[id=tags]').val();
				var num_systems = $('input[id=systems]').val();
				var tag_string;
				if (tag_type == 4)
					tag_string = 'durable';
				else if (tag_type == 1)
					tag_string = 'disposable with bib'


				//*
				$.ajax({
					type: 'POST',
					dataType:'json',
					url: '/api/request_quote/',
					headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
					data: {
						name: name,
						date: startDateTime.toISOString(),
						email: email,
						tag_number: num_tags,
						tag_type: tag_string,
						systems: num_systems,
						price: price,						
					},
					success: function(data) {
						// hide spinner
						//spinner.stop();
						//target.css('height', '');
						
						// show success message
						//$('.notification').hide();
						//$('.notification.create-success').show();

						// switch modals
						$('#order-modal').modal('hide');
						//$('#notifications-modal').modal('show');

						// clear form and reload data

						$('#payment-modal').modal('show');
					},
					error: function(xhr, errmsg, err) {
						// hide spinner
						//spinner.stop();
						//target.css('height', '');
						
						// show error message
						//$('.notification').hide();
						//$('.notification.server-error').show();

						// switch modals
						$('#order-modal').modal('hide');
						//$('#notifications-modal').modal('show');
					}
				});
			});


});
