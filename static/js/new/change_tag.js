$(function() {
    (function init() {
        loadSessions();

        $('.athlete-select').prop('disabled', true);
        $('body').on('change', '.session-select', function() {
            var id = $(this).val();
            loadAthletes(id);
        });
    })();

    $('body').on('click', 'button#submit', function(e) {
        e.preventDefault();
			
        var phone1 = $('input#phone1').val();
        var phone2 = $('input#phone2').val();
        var phone3 = $('input#phone3').val();
        var phone = '+1' + phone1 + phone2 + phone3;
        var session = $('#session-select').val();
        var athlete = $('#athlete-select').val();

        if (!(phone1) || !(phone2) || !(phone3))
            return;
		
        if (!(athlete) || !(athlete))
			return;

        subscribe(session, athlete, phone);
    });

    function loadSessions() {
        $.ajax({
            type: 'GET',
            url: '/api/sessions/',
            dataType: 'json',
            success: function(data) {
                if (data.length === 0)
                    return;

                for (var i=0; i<data.length; i++) {
                    $('#session-select').append(
                        '<option value="'+data[i].id+'">' +
                            data[i].name +
                        '</option>'
                    );
                }
                $('#subscription-select').show();
            }
        });
    }

    function loadAthletes(sessionID) {
        $('#athlete-select').children().first().nextAll().remove();

        $.ajax({
            type: 'GET',
            url: '/api/athletes/?registered_to_session=' + sessionID,
            dataType: 'json',
            success: function(data) {
                for (var i=0; i<data.length; i++) {
                    $('#athlete-select').append(
                        '<option value="' + data[i].id + '">' +
                            data[i].first_name + ' ' + data[i].last_name +
                        '</option>'
                    );
                }
                // enable athlete select
                $('#athlete-select').prop('disabled', false);
            }
        });
    }

    function subscribe(sessionID, athleteID, phone) {
        $.ajax({
            type: 'POST',
            url: '/notifications/subscriptions/',
            data: {
                session: sessionID,
                athlete: athleteID,
                phone_number: phone
            },
            success: function(data) {
                $('#notification-modal').modal('show');
                $('#subscribe-success-message').show();
                $('#subscribe-failure-message').hide();
            },
            error: function(jqXHR, exception) {
                $('#notification-modal').modal('show');
                $('#subscribe-failure-message').show();
                $('#subscribe-success-message').hide();
            }
        });
    }
});
