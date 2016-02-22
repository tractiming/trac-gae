$(function() {

  var tag_type=1, num_tags=25, systems=0;

  $("#tags").keypress(function (e) {
  //if the letter is not digit then display error and don't type anything
  if (e.which != 8 && e.which != 0 && (e.which < 48 || e.which > 57)) {
  return false;
  }
  });


  //Text Change listeners for dynamic pricing
  $("input[name=tag_type]").on('change', function(){
    tag_type = $("input[name=tag_type]:checked").val();
    changePricing(tag_type,num_tags,systems);
  })

  $("#tags").on('input', function(){
    num_tags = $('#tags').val();
    changePricing(tag_type,num_tags,systems);
  });

  $("#systems").on('input', function(){
    systems = $('#systems').val();
    changePricing(tag_type,num_tags,systems);
  });

  function changePricing(tag_type,num_tags,systems){
    price = (tag_type * num_tags) + (systems * 350);
    $('#pricing').text('Price: $' + price+'.00');

  };

  $('#customButton').on('click', function(e) {
      // Open Checkout with further options
      var stripePrice = price;
      $.ajax({
          type: 'POST',
          dataType:'json',
          url: '/payments/charges/',
          headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
          data: {
              amount: stripePrice
          },
          success: function(data) {
              $('#payment-modal').modal('show');
          },
          error: function(xhr, errmsg, err) {
              $('#payment-modal').modal('show');
              $('#success_reference').text('Error. We are unable to process your request');
          }
      });

      e.preventDefault();
  });

   $('#custom-amount').on('click', function(e) {
      // Open Checkout with further options
      if($('#custom-value').val() == ''){
        $('#payment-modal').modal('show');
        $('#success_reference').text('Error. We are unable to process your request');
      }
      else{
      stripePrice = $('#custom-value').val();
      $.ajax({
          type: 'POST',
          dataType:'json',
          url: '/payments/charges/',
          headers: { Authorization: 'Bearer ' + sessionStorage.access_token },
          data: {
              amount: stripePrice
          },
          success: function(data) {
              $('#payment-modal').modal('show');
          },
          error: function(xhr, errmsg, err) {
              $('#payment-modal').modal('show');
              $('#success_reference').text('Error. We are unable to process your request');
          }
      });

      e.preventDefault();
    }
  });

$('#couponButton').on('click', function(e) {
          if($('#coupon').val() == 'flagstaff')
          {
            wait(1500);
            $('#educator').show();
            $('#monthly-button').show();
          }
          else if($('#coupon').val() == 'eugene')
          {
            wait(100);
            $('#custom-price').show();
          }
      });

        function wait(ms){
           var start = new Date().getTime();
           var end = start;
           while(end < start + ms) {
             end = new Date().getTime();
          }
        }
        loadSubscription();

        $('#monthly-button').on('click', function(e) {
            e.preventDefault();
            subscribe('monthly');
        });

        $('#yearly-button').on('click', function(e) {
            e.preventDefault();
            subscribe('yearly');
        });

        $('#yearly-plan-button').on('click', function(e) {
            e.preventDefault();
            subscribe('yearly-plan');
        });
        $('#quarterly-button').on('click', function(e) {
            e.preventDefault();
            subscribe('quarterly');
        });

        function subscribe(plan) {
            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: '/payments/subscription/',
                data: {
                    stripe_plan: plan
                },
                headers: {
                    Authorization: 'Bearer ' + sessionStorage.access_token
                },
                success: function(data) {
                    $('#payment-modal').on('hidden.bs.modal', function() {
                        location.reload(true);
                    });
                    $('#payment-modal').modal('show');
                },
                error: function(xhr, errmsg, err) {
                    $('#payment-modal').modal('show');
                    $('#success_reference').text(
                        'Error. We are unable to process your request');
                }
            });
        }

        function loadSubscription() {
            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/payments/subscription/',
                headers: {
                    Authorization: 'Bearer ' + sessionStorage.access_token
                },
                success: function(data) {
                    if (data.plan == "yearly") {
                        document.getElementById('upgrade-downgrade-monthly')
                            .innerHTML = 'Downgrade';
                        document.getElementById('upgrade-downgrade-yearly')
                            .innerHTML = 'Your current plan';
                        document.getElementById('yearly-button').disabled = true;
                    } else if (data.plan == "monthly") {
                        document.getElementById('upgrade-downgrade-yearly')
                            .innerHTML = 'Upgrade';
                        document.getElementById('upgrade-downgrade-monthly')
                            .innerHTML = 'Your current plan';
                        document.getElementById('monthly-button').disabled = true;
                    }
                    else if (data.plan == "quarterly") {
                        document.getElementById('upgrade-downgrade-yearly-plan')
                            .innerHTML = 'Upgrade';
                        document.getElementById('upgrade-downgrade-quarterly')
                            .innerHTML = 'Your current plan';
                        document.getElementById('quarterly-button').disabled = true;
                    }
                    else if (data.plan == "yearly-plan") {
                        document.getElementById('upgrade-downgrade-quarterly')
                            .innerHTML = 'Upgrade';
                        document.getElementById('upgrade-downgrade-yearly-plan')
                            .innerHTML = 'Your current plan';
                        document.getElementById('yearly-plan-button').disabled = true;
                    }
                },
                error: function(xhr, errmsg, err) {
                }
            });
        }


});