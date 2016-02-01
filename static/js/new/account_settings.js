$(document).ready(function(){

      if (page ==1){
          $('#display-title').text('General');
          $('#edit-password').hide();
          $('#payment').hide()
          $('#athletes').hide();
          $('#edit-information').fadeIn(500);
          $('#team_settings').fadeIn(500);
          loadTeams();
          $.ajax({
                  type: "GET",
                  url: "/api/users/me/",
                  headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
                  success: function(data){
                    $('#edit-information #organization').val('org');
                    $('#edit-information #username').val(data['username']);
                    $('#edit-information #email').val(data['email']);
                  },
                  error: function(xhr, errmsg, err){
                  }
          });
      }
      else if (page == 2){
          $('#display-title').text('Security');
          $('#edit-information').hide();   
          $('#payment').hide(); 
          $('#athletes').hide();
          $('#team_settings').hide();
          $('#edit-password').fadeIn(500);
      }
      else if (page ==3 ){
          $('#team_settings').hide();
          $('#display-title').text('Roster');
          $('#edit-information').hide();   
          $('#athletes').fadeIn(500);       
          $('#edit-password').hide();
          $.ajax({
              url: '/api/athletes/',
              headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
              dataType: 'text',
              success: function(data){
                          $('#athletes').empty();
                          var json = $.parseJSON(data);
                          json = json.reverse();
                          $('#athletes').append(
                                  'Send Athlete Username & Password: <table id="workouts-table" class="table table-striped table-hover">' +
                                        '<thead>' +
                                              '<tr>' +
                                                    '<th class="hidden-xs hidden-sm hidden-md hidden-lg">id</th>'+
                                                    '<th>First Name</th>'+
                                                    '<th>Last Name</th>' + 
                                                    '<th>Username</th>' +
                                                    '<th>Tag ID</th>' + 
                                                    '<th>Email</th>' + 
                                              '</tr>'+
                                        '</thead>'+
                                        '<tbody>'+
                                        '</tbody>' +
                                  '</table>');
                          $('#athletes').addClass('col-md-6 col-md-offset-0 colr-sm-8 col-sm-offset-0');
                          for (var ii=0;ii < json.length;ii++){
               //alert(ii);
                                id = json[ii].id;
                                fname = json[ii].first_name;
                                lname = json[ii].last_name;
                                uname = json[ii].username;
                                tag = json[ii].tag;
                                email = json[ii].email;
                                $('#athletes tbody').append(
                                      '<tr id="formtr" data-href="/individual/'+id+'/">' +
                                          '<td id="id" class="hidden-xs hidden-sm hidden-md hidden-lg"><input id="id" type="text" class="form-control" value="' + id + '" readonly></td>' +
                                          '<td><input id="first_name" type="text" class="form-control" value="'+fname+'" readonly></td>'+
                                          '<td><input id="last_name" type="text" class="form-control" value="'+lname+'" readonly></td>'+
                                          '<td><input id="username" type="text" class="form-control" value="'+uname+'" required readonly></td>' +
                                          '<td><input id="id_str" type="text" class="form-control" value="'+tag+'" required readonly></td>' +
                                          '<td><input id="email" type="text" class="form-control" value="'+email+'" required></td>' +
                                          '<td><input type="button" id="submit" class="form-control btn btn-primary" value="Send Email"></td>'+
                                      '</tr>');
                          }
                    }
          });
          
      }
      $('body').on('click', 'a#e_payment', function(e){
          e.preventDefault();
          location.href='/payments/change/cards/';
      });
      $('#edit-information').on('submit', function(e){
          e.preventDefault();
          var organization = escapeString($('input#organization').val());
          var username = escapeString($('input#username').val());
          var email = escapeString($('input#email').val());
          $.ajax({
                  type: "PATCH",
                  url: "/api/users/me/",
                  headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
                  data: {
                    //org: organization,
                    username: username,
                    email: email,
                  },
                  success: function(data){
                    $('.notification').hide();
                     $('.notification-success').show();
                    $("#success-modal").modal('show');
                  },
                  error: function(xhr, errmsg, err){
                    $('.notification').hide();
                    $('.notification-error').show();
                    $("#success-modal").modal('show');
                  }
          });
      });
      $('#athletes').on('click','input#submit', function(e){
          e.preventDefault();
          var value = $(this).closest('tr');
            var id=value.find('input[id=id]').val();   
            var fname=value.find('input[id=first_name]').val();
            var lname=value.find('input[id=last_name]').val();
            var uname=value.find('input[id=username]').val();
            var id_str=value.find('input[id=id_str]').val();
            var email=value.find('input[id=email]').val();
          //alert(id);
         // alert(fname);
          
          $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/give_athlete_password/",
           headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
               id: id,
               first_name: fname,
               last_name: lname,
               username: uname,
               id_str: id_str,
               email: email,
               
           }, 
                      success: function(data) {
                      $('.notification').hide();
                      $('.notification-success').show();
                      $("#success-modal").modal('show');
                    },
                     error: function(xhr, errmsg, err){
                      $('.notification').hide();
                      $('.notification-error').show();
                      $("#success-modal").modal('show');
                    }
                });
         
      });
      $('#edit-password').on('submit', function(e){
          e.preventDefault();
          $('#edit-password').hide();
          var o_password = escapeString($('input#o_password').val());
          var password = escapeString($('input#n_password').val());
          var c_password = escapeString($('input#c_password').val());
          if(password === c_password){
          $.ajax({
                  type: "POST",
                  url: "/api/users/me/change_password/",
                  headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
                  data: {
                    old_password: o_password,
                    new_password: password,
                  },
                  success: function(data){
                    if (data != 403){
                      $('.notification').hide();
                      $('.notification-success').show();
                      $("#success-modal").modal('show');
                    }
                    else{
                      $('.notification').hide();
                      $('.notification-error').show();
                      $("#success-modal").modal('show');
                    }
                  },
                  error: function(xhr, errmsg, err){
                    alert('Could Not Change Password');
                  }
          });
        }
        else{
          alert('passwords mismatch');
        }
      });  

    $('body').on('click', '#submitTeam', function() {
        // get selected athlete ID
        var id = $('#base-athlete-select').val();
        var team_type = $("input[name=team_type]:checked").val();
        var publicBoolean;
        if (team_type == 'public')
          publicBoolean = true;
        else
          publicBoolean = false;

        $.ajax({
        type: 'PATCH',
        url: '/api/teams/'+id,
        data:{
          public_team: publicBoolean,
        },
        headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
        success: function(data) {
          $('.notification').hide();
          $('.notification-success').show();
          $("#success-modal").modal('show');
          }
        });


      });

    function loadTeams() {

      $.ajax({
        type: 'GET',
        url: '/api/teams/?primary_team=True',
        headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
        dataType: 'json',
        success: function(data) {
          if (data.length === 0) {

            return;
          } 

          for (var i=0; i<data.length; i++) {
            $('#base-athlete-select').append(
              '<option value="'+data[i].id+'">' +
                data[i].name +
              '</option>'
            );

          }
        }
      });
    }
      
});