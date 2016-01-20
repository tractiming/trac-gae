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


	var tag_type=1, num_tags=25, systems=0, startTime = [9,0], startDate, startAMPM, shipping=0;

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

	function changePricing(tag_type,num_tags,systems,diff){
	  price = (tag_type * num_tags) + (systems * 350) + (systems * diff) + (diff/3);
	  $('#pricing').text('Calculated Price: $' + price+'.00');

	};

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

});
