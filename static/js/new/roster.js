  var app = angular.module('raceRegistration', ['ngAnimate','ngRoute']);


   app.controller('registeredCtrl', function($scope, $http) {
    var  SESSIONS_PER_PAGE  = 50;
    $scope.hideInput = true;
    $scope.regNull = false;
    $scope.editing_header = true;
    $scope.currentPage = 1;
    $scope.sessionFirst = 1;
    $scope.sessionLast = SESSIONS_PER_PAGE;
    $scope.universalEdit = false;


    //pagination buttons
    $scope.pageForward = function(){
      $scope.sessionFirst += SESSIONS_PER_PAGE;
      $scope.sessionLast += SESSIONS_PER_PAGE;
      $scope.currentPage++;

      if ($scope.search !== undefined && $scope.search.change.length > 0 )
        var url = '/api/athletes/?registered_to_session='+ $scope.selectedID + '&search=' + $scope.search.change;
      else
        var url = '/api/athletes/?registered_to_session='+ $scope.selectedID +'&limit=50';


      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) { 
          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });

    }
    $scope.pageBackward = function(){
      if ($scope.sessionFirst != 1) {
        $scope.sessionFirst -= SESSIONS_PER_PAGE;
        $scope.sessionLast -= SESSIONS_PER_PAGE;
        $scope.currentPage--;
      }
      if ($scope.search !== undefined && $scope.search.change.length > 0 )
        var url = '/api/athletes/?registered_to_session='+ $scope.selectedID + '&search=' + $scope.search.change;
      else
        var url = '/api/athletes/?registered_to_session='+ $scope.selectedID +'&limit=50';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {
          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });


    }

    $scope.athleteSearch = function(){
      console.log("Search was changed to:"+$scope.search.model);
      $scope.search.change = $scope.search.model;

      var url = '/api/athletes/?registered_to_session='+ $scope.selectedID + '&search=' + $scope.search.change;
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {

          $scope.athletes = response.results;
          $scope.count = response.count;

          if ($scope.count == 0)
            $scope.queryNull = true;
          else
            $scope.queryNull = false;
          
      });

    }

    $scope.searchReset = function(){
      $scope.search.change = '';

      var url = '/api/athletes/?registered_to_session='+ $scope.selectedID;
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {

          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });

    }
    //Load teams for Roster
    var url = '/api/teams/?primary_team=True';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
      .success(function (response) { 
        $scope.rosterTeams = response;
        var rosterCount = response.length;
        $scope.rosterID = $scope.rosterTeams[0].id

          var url = '/api/athletes/?team=' + $scope.rosterID + '&limit=100';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
          .success(function (response) { 

            $scope.rosterAthletes = response.results;

          });
      });

      //Search for Roster
      $scope.athleteSearchRoster = function(){
      $scope.searchRoster.change = $scope.searchRoster.model;
      var url = '/api/athletes/?primary_team=True&search=' +  $scope.searchRoster.change;
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: 100} })
        .success(function (response) {

          $scope.rosterAthletes = response.results;

          if ($scope.count == 0)
            $scope.queryNull = true;
          else
            $scope.queryNull = false;
          
      });

    }

    $scope.searchResetRoster = function(){
      $scope.searchRoster.change = '';

      var url = '/api/athletes/';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {

          $scope.rosterAthletes = response.results;
          
      });

    }


    //Load the heat menu bar on the left hand side of page
    $http({method: 'GET', url: '/api/sessions/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:0, limit:15} })
    .success(function (response) { 
      
      $scope.json = response.results;
      $scope.idArray = response.results.id;
      $scope.temporaryEnd = 15;
      var mostRecentWorkout = response.results[0].id;
      $scope.workoutName = response.results[0].name;
      $scope.selectedID = response.results[0].id;

      //load the roster for the most recent workout\
      var url = '/api/athletes/?registered_to_session='+ mostRecentWorkout+'&limit=50';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
      .success(function (response) { 
        $scope.athletes = response.results;
        $scope.count = response.count;
        if (response.results.length == 0){
           $scope.regNull = true;
        }
        else{
          $scope.regNull = false;
        }

      });

    });

    //onClick event of session in heat menu, dynamically route athletes. 
    $scope.select = function(workout) {
        var selected = workout.id;
        $scope.selectedID = selected;
        $scope.workoutName = workout.name;
        var url = '/api/athletes/?registered_to_session='+ selected+'&limit=50';
        $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
          .success(function (response) { 
            $scope.athletes = response.results;
            //Reset the page counter
            $scope.count = response.count;
            $scope.currentPage = 1;
            $scope.sessionFirst = 1;

            if (response.results.length == 0){
               $scope.regNull = true;
            }
            else{
              $scope.regNull = false;
            }

          });

      };
    //For See More button on Heat Menu
    $scope.seeMore = function(){

      $http({method: 'GET', url: '/api/sessions/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.temporaryEnd, limit:15} })
        .success(function (response) { 
          //merge arrays
        $scope.temporaryEnd += 15;
        $scope.json.push.apply($scope.json, response.results);
      });

    }
    //Deleting an athlete off a workout
    $scope.delete = function(array,index,runner){
      $scope.athletes.splice(index, 1);
      
      //TODO: Do an ajax call, to actually delete
       var url = '/api/athletes/'+runner.id +'/';
       $http({method: 'DELETE', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}})
         .success(function (response) {
          //Update the Count
          var url = '/api/athletes/?registered_to_session='+ $scope.selectedID+'&limit=50';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
            .success(function (response) { 
              $scope.athletes = response.results;
              $scope.count = response.count;

              if (response.results.length == 0){
                 $scope.regNull = true;
              }
              else{
                $scope.regNull = false;
              }
              $scope.universalEdit = false;
          });
       });
    }
        //Deleting an athlete off a workout
    $scope.rosterDelete = function(array,index,runner){
      $scope.rosterAthletes.splice(index, 1);
      
      //TODO: Do an ajax call, to actually delete
       var url = '/api/athletes/'+runner.id +'/';
       $http({method: 'DELETE', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}})
         .success(function (response) {
          //Update the Count
          var url = '/api/athletes/?registered_to_session='+ $scope.selectedID+'&limit=50';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
            .success(function (response) { 
              $scope.athletes = response.results;
              $scope.count = response.count;

              if (response.results.length == 0){
                 $scope.regNull = true;
              }
              else{
                $scope.regNull = false;
              }
              $scope.universalEdit = false;
          });
       });
    }

    //Editing an athletes info for a workout
    $scope.save = function(runner){
      var url = '/api/athletes/'+runner.id +'/';
      $http({method: 'PATCH', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        first_name: runner.first_name,
        last_name: runner.last_name,
        username: runner.username,
        tag: runner.tag,
        team: runner.team,
        birth_date: runner.birth_date,
        gender: runner.gender,

       } 
      })
        .success(function (response) { 
          $scope.universalEdit = false;
          var dynamicString = 'editing_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'showDelete_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'showSave_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'editing_icons_' + runner.id;
          $scope[dynamicString] = false;
      });
    }

    // editing contact info
    $scope.editing = false;
    $scope.edit = function(x) {
       var dynamicIndex = x.id;
       $scope.newField = angular.copy(x);

      if ($(window).width() < 768) {
        $scope.val = x;
        // do something for small screens
        //$('#editAthlete').modal('show');

      }
      else if ($(window).width() >= 768 &&  $(window).width() <= 992) {
          // do something for medium screens
          $('#editAthlete').modal('show');
          $scope.val = x;
      }
      else  {
        var dynamicString = 'editing_' + x.id;
        $scope[dynamicString] = true;
          // do something for huge screens
      }
     // var selectedID = angular.element(obj.target).parent().parent().parent().attr('id');
      
    };


    $scope.cancel = function(x) { 

      var selectedID = x.id;
      var tempIndex = $scope.athletes.indexOf(x);
      //Resore old data as necessary, only if editing
      var dynamicString = 'editing_' + selectedID;
      if ($scope[dynamicString] == true){
        $scope.athletes[tempIndex] = $scope.newField;
        $scope[dynamicString] = false;
      }
      
      var dynamicString = 'showDelete_' + selectedID;
      $scope[dynamicString] = false;
      var dynamicString = 'showSave_' + selectedID;
      $scope[dynamicString] = false;
      var dynamicString = 'editing_icons_' + selectedID;
        $scope[dynamicString] = false;
      var dynamicString = 'showEdit_' + x.id;
        $scope[dynamicString] = false;

      $scope.universalEdit = false;
    };

      $scope.rosterCancel = function(x) { 

      var selectedID = x.id;
      var tempIndex = $scope.rosterAthletes.indexOf(x);
      //Resore old data as necessary, only if editing
      var dynamicString = 'editing_' + selectedID;
      if ($scope[dynamicString] == true){
        $scope.rosterAthletes[tempIndex] = $scope.newField;
        $scope[dynamicString] = false;
      }
      
      var dynamicString = 'showDelete_' + selectedID;
      $scope[dynamicString] = false;
      var dynamicString = 'showSave_' + selectedID;
      $scope[dynamicString] = false;
      var dynamicString = 'editing_icons_' + selectedID;
        $scope[dynamicString] = false;
      var dynamicString = 'showEdit_' + x.id;
        $scope[dynamicString] = false;

      $scope.universalEdit = false;
    };

    //This is pretty jQuery heavy....
    $scope.showSelected = function(){
      var atlList = [];
      $('#rosterModal tr.ath').each(function(){
        var atlObj = {};
        if ($(this).find('td #check').is(":checked")){
          atlObj = $(this).children('#id').text();
          atlList.push(atlObj);
        }
      });
      //Get the pk and data from row and send to server
      var url = '/api/sessions/'+ $scope.selectedID +'/register_athletes/';
      $http({method: 'POST', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        athletes: atlList,
       } 
      })
        .success(function (response) {
          var url = '/api/athletes/?registered_to_session='+ $scope.selectedID+'&limit=50';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
            .success(function (response) { 
              $scope.athletes = response.results;
              $scope.count = response.count;
              
              if (response.results.length == 0){
                 $scope.regNull = true;
              }
              else{
                $scope.regNull = false;
              }
          });
        });

      $('#rosterModal').modal('hide');
    }
    $scope.header = function(){
      $scope.editing_header = false;
    }
    $scope.cancelHeader = function(){
      $scope.editing_header = true;
    }
    $scope.saveHeader = function(regForm){
      $http({method: 'POST', url: '/api/athletes/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        first_name: regForm.first_name,
        last_name: regForm.last_name,
        username: regForm.first_name+regForm.last_name,
        tag: regForm.tag,
        birth_date : regForm.birth_date,
        team: $scope.rosterID,

       } 
      })
        .success(function (response) {

          var url = '/api/athletes/?team=' + $scope.rosterID + '&limit=100';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
          .success(function (response) { 

            $scope.rosterAthletes = response.results;
          });
          $scope.editing_header = true;
          $('.expand').val('');

      });

    }
    $scope.deleteButtons = function(x){
        $scope.universalEdit = true;
        var dynamicString = 'editing_icons_' + x.id;
        $scope[dynamicString] = true;
        var dynamicString = 'showDelete_' + x.id;
        $scope[dynamicString] = true;

    }
    $scope.saveButtons = function(x){
        $scope.universalEdit = true;
        var dynamicString = 'editing_icons_' + x.id;
        $scope[dynamicString] = true;
        var dynamicString = 'showSave_' + x.id;
        $scope[dynamicString] = true;

    }
    $scope.workoutRemove = function(x){
        $scope.universalEdit = true;
        var dynamicString = 'editing_icons_' + x.id;
        $scope[dynamicString] = true;
        var dynamicString = 'showEdit_' + x.id;
        $scope[dynamicString] = true;

    }

    $scope.remove = function(array,index,runner){
      $scope.athletes.splice(index, 1);
      var url = '/api/sessions/'+ $scope.selectedID +'/remove_athletes/';
      $http({method: 'POST', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        athletes: [runner.id]} })
        .success(function (response) { 
          $scope.universalEdit = false;
          var url = '/api/athletes/?registered_to_session='+ $scope.selectedID+'&limit=50';
          $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
            .success(function (response) { 
              $scope.athletes = response.results;
              $scope.count = response.count;
              if (response.results.length == 0){
                 $scope.regNull = true;
              }
              else{
                $scope.regNull = false;
              }
          });

      });

    }


    //Keep style consistent during animations of search bar
    $scope.changeStyle = function(toggle){
      var buttonStyle = 'border-bottom-right-radius: 4px !important; border-top-right-radius : 4px !important; border-right:1px solid #ccc !important;';
      var buttonStyle2 = 'border-bottom-right-radius: 0px !important; border-top-right-radius : 0px !important; border-right:0 !important;';
      if (toggle == true) {
        return buttonStyle;
      }
      else{
        return buttonStyle2;
      }
    }
    $scope.hoverIn = function(){
      if(!$scope.universalEdit)
        this.hoverEdit = {display:'inline-block'};
    };

    $scope.hoverOut = function(){
        this.hoverEdit = {display:'none'};
    };

  });

 


   