
	$(document).ready(function(){
    // initialize spinner
     var opts = {
        lines: 13,              // The number of lines to draw
        length: 28,             // The length of each line
        width: 14,              // The line thickness
        radius: 42,             // The radius of the inner circle
        scale: 0.5,             // Scales overall size of the Spinner
        corners: 1,             // Corner roundness (0..1)
        color: '#3577a8',       // #rgb or #rrggbb or array of colors
        opacity: 0.25,          // Opacity of the lines
        rotate: 0,              // The rotation offset
        direction: 1,           // 1: clockwise, -1: counterclockwise
        speed: 1,               // Rounds per second
        trail: 60,              // Afterglow percentage
        fps: 20,                // Frames per second when using setTimeout() as a fallback for CSS
        zIndex: 1,              // The z-index (defaults to 2000000000)
        className: 'spinner',   // The CSS class to assign to the spinner
        top: '50%',             // Top position relative to parent
        left: '50%',            // Left position relative to parent
        shadow: false,          // Whether to render a shadow
        hwaccel: false,         // Whether to use hardware acceleration
        position: 'relative'    // Element positioning
      }
      var target = document.getElementById('spinner');
      var modal_target = document.getElementById('spinner_modal');
      var spinner = new Spinner(opts);
	if (sessionStorage.usertype == 'athlete'){
		$("div.right").hide();
		 $('div.pictures').css('padding-left','200px');
		 $('div.text').css('padding-left','200px');
		}
    
    loadAthletes();
    var pushyheight = $('.pushy').height();
    var itemheight = 56;
    numitems = pushyheight / itemheight;
    numitems = Math.floor(numitems);
    instance_last = numitems;
    findScores();
    loadRoster();

  // add feedback on file selection
  $('.btn-file :file').off('fileselect');
  $('.btn-file :file').on('fileselect', function(e, numFiles, label) {
    var input = $(this).parents('.input-group').find(':text'),
        log = numFiles > 1 ? numFiles + ' files selected' : label;

    if( input.length ) {
      input.val(log);
    } else {
      if( log ) alert(log);
    }
  });

  // trigger event on file selection
  $('body').off('change', '.btn-file :file');
  $('body').on('change', '.btn-file :file', function() {
    var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');

    input.trigger('fileselect', [numFiles, label]);
  });

 function loadRoster(){
    $('#roster').empty();
        $.ajax({
                    url: "api/athletes/",
                    headers: {Authorization: "Bearer " + sessionStorage.access_token},
                    dataType: 'text',
                    success: function(data){
                          var json = $.parseJSON(data);
                          json = json.reverse();

                          $('#roster').append(
                                  '<table id="workouts-table" class="table table-striped table-hover">' +
                                        '<thead>' +
                                              '<tr>' +
                                              '<th></th>' +
                                                    '<th class="hidden-xs hidden-sm hidden-md hidden-lg">id</th>'+
                                                    '<th>Name</th>'+
                                                    '<th>Tag ID</th>' + 
                                                    '<th style="display:none">Username</th>' + 
                                              '</tr>'+
                                        '</thead>'+
                                        '<tbody>'+
                                        '</tbody>' +
                                  '</table>');
                          $('#roster').addClass('col-md-6 col-md-offset-0 colr-sm-8 col-sm-offset-0');
                          

                          for (var ii=0;ii < json.length;ii++){
               //alert(ii);  
                         
                                id = json[ii].id;
                                fname = json[ii].user.first_name;
                                lname = json[ii].user.last_name;
                                uname = json[ii].user.username;
                                tag_nest = json[ii].tag;
                                //Tags no Longer are nested
                                //var unnested_tags = $.parseJSON(tag_nest);
                                //user_tag = unnested_tags.ids[0];

                                $('#roster tbody').append(
                                      '<tr class="ath">'+
                                          '<td><input type="checkbox" id="check" style="width:12px; height:12px;"/></td>' +
                                          '<td class="hidden-xs hidden-sm hidden-md hidden-lg">' + id + '</td>' +
                                          '<td id="fname" style="display:none">'+fname+'</td>'+
                                          '<td id="lname" style="display:none">'+lname+'</td>'+
                                          '<td id="uname" style="display:none">'+uname+'</td>' +
                                          '<td id="full_name">'+fname+' '+lname+'</td>'+
                                         '<td id="u_tag">'+tag_nest+'</td>' +
                                      '</tr>');
                          }
                    }
              });
  }
  function loadAthletes(){
    spinner.spin(target);
   $('#athletes').empty();
   if (id_helper!=0){
   $.ajax({
    url: "api/reg_tag/",
    headers: {Authorization: "Bearer " + sessionStorage.access_token},
    data: {id: id_helper},
    dataType: 'text',
    success: function(data){
      var json = $.parseJSON(data);
      json = json.reverse();
      spinner.stop();
      $('p#inputnoneheader').hide();
      $('p#inputheader').hide();
      if(json.length==0){
           $('p#inputnoneheader').show();
            return
       }
                          
        $('#athletes').append(
          '<table id="results-table" class="table table-striped table-hover">' +
              '<thead>' +
                  '<tr>' +
                    '<th class="hidden-xs hidden-sm hidden-md hidden-lg">id</th>'+
                    '<th>Name</th>'+
                    '<th style="display:none">Username</th>'+
                    '<th>Tag ID</th>' +
                  '</tr>'+
                '</thead>'+
                '<tbody>'+
                '</tbody>'+
              '</tbody>');
        $('#athletes').addClass('col-md-6 col-md-offset-0 colr-sm-8 col-sm-offset-0');
        for (var ii=0;ii < json.length;ii++){
               id = json[ii].id;
               fname = json[ii].first;
               lname = json[ii].last;
               tag = json[ii].id_str;
               uname = json[ii].username;
               age = json[ii].age;
               gender = json[ii].gender;
               
                $('#athletes tbody').append(
                  '<tr>'+
                    '<td class="hidden-xs hidden-sm hidden-md hidden-lg">' + id + '</td>' +
                    '<td>'+fname+' '+lname+'</td>'+
                    '<td style="display:none">'+fname+'</td>'+
                    '<td style="display:none">'+lname+'</td>'+
                    '<td style="display:none">'+uname+'</td>'+
                    '<td>'+tag+'</td>' +
                    '<td style="display:none">'+age+'</td>'+
                    '<td style="display:none">'+gender+'</td>'+
                  '</tr>');
      }
            $('#inputheader').hide();
    }
   });
    }
    else{
      spinner.stop();
      $('#inputheader').show();
    }
}

    function findScores(){
      //spinner.spin(target);

      $.ajax({
        url: '/api/sessions/',
        headers: {Authorization: 'Bearer ' + sessionStorage.access_token},
        dataType: 'text',     //force to handle it as text
        data: {
          offset: sessionFirst-1,
          limit: 15,
        },
        success: function(data){
          var json = $.parseJSON(data);

          var results = json.results,
          numSessions = json.count;
          
          if ((results.length == 0) && (!$.trim($('ul.menulist').html()))) {
            
            spinner.stop();
          } else {
            
            for (var i=0; i<results.length; i++){
              // add events to event menu
              $('ul.menulist').append('<li><a href="#">'+results[i].name+'</a></li>');
              idArray.push(results[i].id);
            }
            if (results.length == 15){
              $('ul.menulist').append('<li id="see-more"><a href="#">See More</a></li>');
            }
          }
          // show most recent workout, edit: do not show more recent workout
          currentID = currentID || idArray[0];
          //update(currentID, currentView);
        }
      });
    }
function resetScores(){
    $('#linkedlist tr#sM').remove();
    $('ul.menulist li#sM').remove();
  }
  // attach handler for heat menu item click

    var stepped = 0, rowCount = 0, errorCount = 0, firstError;
    var inputType = "string";

      
      $("#csvform").on('submit', function(e){
      e.preventDefault();

      $("#csvform").parsley().validate();
      if (!$("#csvform").parsley().isValid()){
        return;
      }
      var config = buildConfig();
      
$('#file').parse({
      config:config,
      before: function(file, inputElem)
        {
          $(modal_target).css("height",100);
          spinner.spin(modal_target);
          $("#csv_buttons").hide();


          start = now();
          console.log("Parsing file...", file);
        },
        error: function(err, file)
        {
          console.log("ERROR:", err, file);
          firstError = firstError || err;
          errorCount++;
        },
      
      complete: function(){
        end = now();
        printStats("Done with all files");
        
        
        
      }
    });
  });

  function now()
{
  return typeof window.performance !== 'undefined'
      ? window.performance.now()
      : 0;
}
function buildConfig()
{
  return {
    delimiter: '',
    header: true,
    dynamicTyping: false, //turn numbers into numbers or strings? yes no to boolean?
    skipEmptyLines:true,
    preview: parseInt($('#preview').val() || 0),
    step: $('#stream').prop('checked') ? stepFn : undefined,
    encoding: '',
    worker: true, //run on separate thread--slower but wont lock webpage
    comments: $('#comments').val(),
    complete: completeFn,
    error: errorFn,
    download: inputType == "remote"
  };
}
function stepFn(results, parser)
{
  stepped++;
  if (results)
  {
    if (results.data)
      rowCount += results.data.length;
    if (results.errors)
    {
      errorCount += results.errors.length;
      firstError = firstError || results.errors[0];
    }
  }
}
function completeFn(results)
{
  end = now();
  if (results && results.errors)
  {
    if (results.errors)
    {
      errorCount = results.errors.length;
      firstError = results.errors[0];
    }
    if (results.data && results.data.length > 0)
      rowCount = results.data.length;
      
  }
  printStats("Parse complete");
  console.log("    Results:", JSON.stringify(results.data));
  var dated = $('input[id=date]').val();
  var reads = $('input[id=readers]').val();
  var workoutName = $('input[id=name]').val();
  var username =$('input[id=coach_username]').val();
  //I made a manipulated string that allows users to input a list of readers and separates each reader.
  var readersList = reads.split(",");
  var rL = "";
  for(var j = 0; j < readersList.length; j++){
    rL = rL.concat('"'+readersList[j]+'"');
    if (j != readersList.length - 1){
      rL = rL.concat(',');
    }
  }
  rL = '['+rL+']';
  rL = rL.replace(/\s/g, '');
  dL = local2UTC(dated);
  console.log(dL);
  //The manipulated string matches the api conventions and successfully creates new races with the readers that user inputs.
  var json = '{"race_name":"'+workoutName+'","race_date":"'+dL+'","director_username":"'+username+'","readers":'+rL+',"athletes":'+JSON.stringify(results.data)+'}';
  console.log(json);
  $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/raceregistration/",
     headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data:json,
           // Login was successful.
           success: function(data) {alert('Successful Submission'); resetScores(); $('ul.menulist').empty(); findScores(); $(modal_target).css("height",""); spinner.stop(); $("#csv_buttons").show(); $('#csvModal').modal('hide');},
           error: function(xhr, errmsg, err) {alert('Upload Error'); $(modal_target).css("height",""); spinner.stop(); $("#csv_buttons").show();}
     });
      
      $('#file').val('');
  // icky hack
  //setTimeout(enableButton, 100);
}
function errorFn(err, file)
{
  end = now();
  console.log("ERROR:", err, file);
  //enableButton();
}
function printStats(msg)
{
  if (msg)
    console.log(msg);
  console.log("       Time:", (end-start || "(Unknown; your browser does not support the Performance API)"), "ms");
  console.log("  Row count:", rowCount);
  if (stepped)
    console.log("    Stepped:", stepped);
  console.log("     Errors:", errorCount);
  if (errorCount)
    console.log("First error:", firstError);
}

$("body").on('click', '#athletes tr' ,function(){
  $('#myModal').modal('toggle');
  var value = $(this).html();
  $("button#delete2").show();
  $("button#update2").show();
  $("div.button-container-two").show();
  $("input#create").show();
  $("p#idnumber").show();
  $("button#save2").hide();
  $(value).each(function(index){
    //alert( $(this).html() );
    console.log( index+ ":"+ $(this).html());
    if (index ==0)
    {
      var input =$('input#idnumber');
      input.val($(this).html() );
    }
    else if (index ==2)
    {
      var input =$('input#fname');
      input.val($(this).html() );
      }
      else if (index ==3)
    {
      var input =$('input#lname');
      input.val($(this).html() );
      }
      else if (index ==4)
    {
      var input =$('input#uname');
      input.val($(this).html() );
      }
    else if (index ==5)
    {
      var input =$('input#tag');
      input.val($(this).html() );
      }
    else if (index ==6)
    {
      var input =$('input#age');
      input.val($(this).html() );
      }
    else if (index ==7)
    {
      var input =$('input#gender');
      input.val($(this).html() );
      }
  });
});

/*$("body").on('click', 'button#plus', function(e){
  //alert($(this).html());
    e.preventDefault();
    $("#coachform")[0].reset();
  var value = $(this).html();
  $("button#delete").hide();
  $("input#update").hide();
  $("input#save").show();
  $("p#idnumber").hide();
  //$("input#create").hide();

  });
*/
$("button#delete2").off('click');
  $("body").on('click', 'button#delete2', function(f){
  //alert($(this).html());
    f.preventDefault();
    $(".notification").hide();
    $(".notification.notification-warning").show();
    $("button#warning-yes").hide();
    $("button#warning-yes2").show();

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
$('body').on('click', '#register', function(e){
  var atlList = [];
  $('#roster tr.ath').each(function(){
      var atlObj = {};
      if ($(this).find('td #check').is(":checked")){
          atlObj.first_name = $(this).children('#fname').text();
          atlObj.last_name = $(this).children('#fname').text();
          atlObj.username = $(this).children('#uname').text();
          atlList.push(atlObj);
      }
  });
  var json = '{"id":"'+id_helper+'", "athletes":'+JSON.stringify(atlList)+'}';
  //console.log(json);
  $.ajax({
    type: 'POST',
    dataType: 'json',
    url: '/api/reg_manytags/',
    data: json,
    headers: {Authorization: "Bearer " + sessionStorage.access_token},
    success: function(data){
      resetScores();
      $('ul.menulist').empty();
      findScores();
      loadAthletes();
    },
    error: function(xhr, errmsg, err){
      //alert ("No athletes selected");
    }
  });
});
$("body").on('click', '#open', function(e){
  if(id_helper == 0){
    $('.notification').hide();
     $('.notification-critical').show();
   return
  }
          $.ajax({

              type: 'POST',
              dataType: 'json',
              url: '/api/sessions/'+id_helper+'/open/',
              headers: {Authorization: "Bearer " + sessionStorage.access_token},
              success: function(data){

                 $('.notification').hide();
                     $('div.notification.open-success').show();
                 // isOpen = true;
              },
              error: function(xhr, errmsg, err){
                 // alert ("session couldn't open");
                 $('.notification').hide();
                 $('.notification-critical').show();
              }
          });
});

$("body").on('click', 'button#stop', function(e){
            if(id_helper == 0){
              $('.notification').hide();
               $('.notification-critical').show();
                return
            }
            else{
            $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: '/api/sessions/'+id+'/close/',
                    //data: {id: id},
                    headers: {Authorization: "Bearer " + sessionStorage.access_token},
                    success: function(data){
                     // alert ('session closed');
                      $('.notification').hide();
                     $('div.notification.close-success').show();
                     // isOpen=false;
                    },
                    error: function(xhr, errmsg, err){
                     // alert ("couldn't close session");
                     $('.notification').hide();
                     $('.notification-critical').show();
                    }
            });
          }
});

$("body").on('click', 'button#start', function(e){
            if(id_helper == 0){
              $('.notification').hide();
                $('.notification-critical').show();
               return
              }
            else{
            $.ajax({
                    type: 'POST',
                    dataType: 'json',
                    url: '/api/sessions/'+id+'/start_timer/',
                    headers:{Authorization: "Bearer " + sessionStorage.access_token},
                    success: function(data){
                     // alert ('session started');
                     $('.notification').hide();
                     $('div.notification.start-success').show();

                    },
                    error: function(xhr, errmsg, err){
                    //  alert ("couldn't start session");
                    $('.notification').hide();
                    $('.notification-critical').show();
                    }
            });
          }
});


    // attach handler for heat menu item click
    $('body').on('click', 'ul.menulist li a', function(){
      var value = $(this).html();
      if (value == 'See More'){
        sessionFirst += 15;
        sessionLast += 15;
        $('ul.menulist li#see-more').remove();
        findScores();
      } else {
        var indexClicked = $( 'ul.menulist li a' ).index( $(this) );
        
        // reset canvases and set new session id
        $('.notification').hide();

        currentID = idArray[indexClicked];
        id_helper = currentID;
        loadAthletes();
        //spinner.spin(target);
        //update(currentID, currentView);
      }
    });


   $("body").on('click','button#update2', function(e){
         e.preventDefault();
         	var it=$('input[id=idnumber]').val();   
            var uname=$('input[id=uname]').val();
            var fname=$('input[id=fname]').val();
            var lname=$('input[id=lname]').val();
            var ti=$('input[id=tag]').val();
            var age=$('input[id=age]').val();
            var gender=$('input[id=gender]').val();
            console.log(fname);
        $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/reg_tag/",
           headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
           	   id: id_helper,
           	   id2: it,
               username: uname,
               id_str: ti,
               firstname:fname,
               lastname:lname,
               age:age,
               gender:gender,
               submethod: 'Update'
           }, 
                      success: function(data) {
                      //console.log(fname);
                      $("#coachform")[0].reset();
                      loadAthletes();
                      loadRoster();
                      $(".notification").hide();
                      $(".notification.update-success").show();
                    
                    },
                     error: function(xhr, errmsg, err){
        alert ("couldn't find workout");
      }
                });
           
      });

$("body").on('click', '#roster tr' ,function(e){
   var target = $( event.target );
  if ( target.is( "input" ) ) {
    return;
  }
  $('#athleteModal').modal('toggle');
  var value = $(this).html();
  $("button#delete").show();
  $("button#update").show();
  $("div.button-container-two").show();
  //$("input#create").show();
  $("p#idnumber").show();
  //$("label#id_str").hide();
  //$("input#id_str").hide();
  $("button#save").hide();
  $(value).each(function(index){
    //alert( $(this).html() );
    //console.log( index+ ":"+ $(this).html());
    if (index ==1)
    {
      var input =$('input#idnumber2');
      input.val($(this).html() );
    }
    else if (index ==2)
    {
      var input =$('input#first_name');
      input.val($(this).html() );
      }
    else if (index == 3)
    {
      var input = $('input#last_name');
       input.val($(this).html() );
    }
    else if (index == 6)
    {
      var input = $('input#id_str');
       input.val($(this).html() );
    }
  });

});

$("body").on('click', 'button#plus2', function(e){
  //alert($(this).html());
    e.preventDefault();
    $("#rosterform")[0].reset();
  var value = $(this).html();
  $("button#delete").hide();
  $("button#update").hide();
  $("button#save").show();
  $("p#idnumber").hide();
  $("label#id_str").show();
  $("input#id_str").show();
  //$("input#create").hide();

  });

//Both Delete buttons link to same modal
$("button#delete").off('click');
  $("body").on('click', 'button#delete', function(f){
  //alert($(this).html());
    f.preventDefault();
    $(".notification").hide();
    $("div.notification.notification-warning").show();
    $("button#warning-yes").show();
    $("button#warning-yes2").hide();
    
    
  });

//Roster Delete Warning Button 
  $("body").on('click', 'button#warning-yes', function(event){
  //console.log("On:", event.target);
  var value = $(this).html();
   $(".modal-animate").show();
    
   var id=$('input[id=idnumber2]').val();
   console.log("On:", id);
  //alert(id);
  
    //alert(filter);
        $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/edit_athletes/",
           data:
           {id: id,
          submethod: 'Delete'},
          headers: {Authorization: "Bearer " + sessionStorage.access_token},
         
           // Login was successful.
           success: function(data) {
                  $(".modal-animate").hide();
                  $(".notification").hide();
                  $(".notification.delete-success").show();
                 
                $("#coachform")[0].reset();
               $("button#delete").hide();
               $("input#update").hide();
                $("input#save").show();
                 $("p#idnumber").hide();
                 //$("input#create").hide();
                  $("#athletes").empty();
                 loadRoster();
              },
              // Login request failed.
           error: function(xhr, errmsg, err) {
      //hide spinner, show error modal
      $(".modal-animate").hide();
     $(".notification").hide();
        $(".notification.notification-critical").show();
           }
            });  
});

//Unlink Delete Button
$("body").on('click', 'button#warning-yes2', function(event){
          var it=$('input[id=idnumber]').val();   
            var fname=$('input[id=username]').val();
            var ti=$('input[id=tag]').val();
            //console.log(fname);
        $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/reg_tag/",
           headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
               id: id_helper,
               id2: it,
               username: fname,
               id_str: ti,
               submethod: 'Delete'
           }, 
         
         
           // Login was successful.
           success: function(data) {
                  $(".modal-animate").hide(); 
                  $(".notification").hide();
                  $(".notification.delete-success").show();
                 
                $("#coachform")[0].reset();
               $("button#delete").hide();
               $("input#update").hide();
                $("input#save").show();
                 $("p#idnumber").hide();
                 //$("input#create").hide();
                  $("#athletes").empty();
                 loadAthletes();
              },
              // Login request failed.
           error: function(xhr, errmsg, err) {
      //hide spinner, show error modal
      $(".modal-animate").hide();
      $(".notification").hide();
        $("notification.notification-critical").show();
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
$("body").on('click', 'button#cl', function(e){
  e.preventDefault();
  $('div#tutorial').slideUp();
});

//Roster Update
   $("body").on('click','button#update', function(e){
         e.preventDefault();
          var id=$('input[id=idnumber2]').val();   
            var fname=$('input[id=first_name]').val();
            var lname=$('input[id=last_name]').val();
            var tagid=$('input[id=id_str]').val();
        $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/edit_athletes/",
           headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
               id: id,
               first_name: fname,
               last_name: lname,
               id_str:tagid,

               submethod: 'Update'
           }, 
                      success: function(data) {
                      $("#coachform")[0].reset();
                      loadRoster();
                      $(".notification").hide();
                      $(".notification.update-success").show();
                    }
                });
           
      });

//Roster Save Button
   $("body").on('click','button#save', function(e){

         e.preventDefault();
         var form = $(this);  
        $("#rosterform").parsley().validate();
         if ( $("#rosterform").parsley().isValid()){ 
            var fname=$('input[id=first_name]').val();
            var lname=$('input[id=last_name]').val();
            var tag = $('input[id=id_str]').val();
        $.ajax({
           type: "POST",
           dataType:'json',
           url: "/api/edit_athletes/",
           headers: {Authorization: "Bearer " + sessionStorage.access_token},
           data: {
               first_name: fname,
               last_name: lname,
               username: fname + "" + lname,
               id_str: tag,
               submethod: 'Create',
           }, 
                      success: function(data) {
                      $("#rosterform")[0].reset();
                      loadRoster();
                      $('#athleteModal').modal('hide');
                    }
                });
           }
      });
});
