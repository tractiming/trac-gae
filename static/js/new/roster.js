  var app = angular.module('raceRegistration', ['ngAnimate','ngRoute']);


   app.controller('registeredCtrl', function($scope, $http) {
    var  SESSIONS_PER_PAGE  = 5;
    $scope.hideInput = true;
    $scope.regNull = false;
    $scope.editing_header = true;
    $scope.currentPage = 1;
    $scope.sessionFirst = 1;
    $scope.sessionLast = SESSIONS_PER_PAGE;


    //pagination buttons
    $scope.pageForward = function(){
      $scope.sessionFirst += SESSIONS_PER_PAGE;
      $scope.sessionLast += SESSIONS_PER_PAGE;
      $scope.currentPage++;

      if ($scope.search.change.length > 0)
        var url = '/api/athletes/?search=' + $scope.search.change;
      else
        var url = '/api/athletes/';


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
      if ($scope.search.change.length > 0)
        var url = '/api/athletes/?search=' + $scope.search.change;
      else
        var url = '/api/athletes/';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {
          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });


    }

    $scope.athleteSearch = function(){
       console.log("Search was changed to:"+$scope.search.model);
      $scope.search.change = $scope.search.model;

      var url = '/api/athletes/?search=' +  $scope.search.change;
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {

          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });

    }

    $scope.searchReset = function(){
      $scope.search.change = '';

      var url = '/api/athletes/';
      $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) {

          $scope.athletes = response.results;
          $scope.count = response.count;
          
      });

    }

    //load the roster for the most recent workout
    $http({method: 'GET', url: '/api/athletes/?limit=5', headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
    .success(function (response) { 
      $scope.athletes = response.results;
      $scope.count = response.count;
      if (response.length == 0){
        $scope.regNull = true;
      }

    });

    //Load the heat menu bar on the left hand side of page
    $http({method: 'GET', url: '/api/sessions/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:0, limit:15} })
    .success(function (response) { 
      
      $scope.json = response.results;
      $scope.idArray = response.results.id;
      $scope.temporaryEnd = 15;

    });

    //onClick event of session in heat menu, dynamically route athletes. 
    $scope.select = function(workout) {
        var selected = workout.id;
        $scope.selectedID = selected;
        $scope.workoutName = workout.name;
        var url = '/api/athletes/?session='+ selected+'limit=50';
        $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
          .success(function (response) { 
            $scope.athletes = response;
            if (response.length == 0){
               $scope.regNull = true;
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

      $http({method: 'GET', url: '/api/athletes/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, params:{offset:$scope.sessionFirst-1, limit: SESSIONS_PER_PAGE} })
        .success(function (response) { 
          $scope.athletes = response.results;
          $scope.count = response.count;
          
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
        tag: runner.first_name,
        team: runner.team,
        birth_date: runner.birth_date,
        gender: runner.gender,

       } 
      })
        .success(function (response) { 
         alert('successfully changed');
          var dynamicString = 'editing_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'showDelete_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'showSave_' + runner.id;
          $scope[dynamicString] = false;
          var dynamicString = 'editing_icons_' + runner.id;
          $scope[dynamicString] = false;
      });
      //TODO: Do an ajax call, to actually save
    }

    // editing contact info
    $scope.editing = false;
    $scope.edit = function(x) {
       var dynamicIndex = x.id;
       $scope.newField = angular.copy(x);

      if ($(window).width() < 768) {
        $scope.val = x;
        // do something for small screens
        $('#editAthlete').modal('show');

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
      alert(atlList);
      var url = '/api/sessions/'+ $scope.selectedID +'/';
      alert(url);
      $http({method: 'PATCH', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        registered_athletes: [atlList],
       } 
      })
        .success(function (response) { 
         alert('successfully changed');
      });

      $('#rosterModal').modal('hide');
    }
    $scope.header = function(){
      $scope.editing_header = false;
    }
    $scope.cancelHeader = function(){
      $scope.editing_header = true;
    }
    $scope.saveHeader = function(runner){
      $http({method: 'POST', url: '/api/athletes/', headers: {Authorization: 'Bearer ' + sessionStorage.access_token}, data:{
        user:{
        first_name: runner.user.first_name,
        last_name: runner.user.last_name,
        username: runner.user.username,
        },
        tag: runner.tag,
        team: runner.team,

       } 
      })
        .success(function (response) { 
         alert('successfully changed');
      });

    }
    $scope.deleteButtons = function(x){
        var dynamicString = 'editing_icons_' + x.id;
        $scope[dynamicString] = true;
        var dynamicString = 'showDelete_' + x.id;
        $scope[dynamicString] = true;

    }
    $scope.saveButtons = function(x){
        var dynamicString = 'editing_icons_' + x.id;
        $scope[dynamicString] = true;
        var dynamicString = 'showSave_' + x.id;
        $scope[dynamicString] = true;

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
  });
   