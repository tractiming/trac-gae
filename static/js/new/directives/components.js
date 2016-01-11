'use strict';

/**
 * @ngdoc directive
 * @name: tabs & pane
 * @description
 * # tabs and pane
 */


 
  angular.module('raceRegistration').directive('tabs', function(usSpinnerService) {
    return {
      restrict: 'E',
      transclude: true,
      scope: {
        rosterAthletes:'=',
        rosterID:'='
      },
      controller: function($scope, $element, $http) {
        var panes = $scope.panes = [];
 
        $scope.select = function(pane) {
          angular.forEach(panes, function(pane) {
            pane.selected = false;
          });
          pane.selected = true;
        }

        $scope.getRoster = function(id){
          if (id == 'addTeam'){
          }
          else {
          usSpinnerService.spin('roster-spinner');
          var url = '/api/athletes/?team=' + id + '&limit=100';
            $http({method: 'GET', url: url, headers: {Authorization: 'Bearer ' + sessionStorage.access_token} })
            .success(function (response) { 

              $scope.$parent.rosterAthletes = response.results;
              $scope.$parent.rosterID = id;
              usSpinnerService.stop('roster-spinner');
            });
          }
        }

 
        this.addPane = function(pane) {
          if (panes.length == 0) $scope.select(pane);
          panes.push(pane);
        }
      },
      template:
        '<div class="tabbable">' +
          '<ul class="nav nav-tabs">' +
            '<li ng-repeat="pane in panes" ng-class="{active:pane.selected}" role="presentation">'+
              '<a href="" ng-click="select(pane); getRoster(pane.id)">{{pane.title}}</a>' +
            '</li>' +
          '</ul>' +
          '<div class="tab-content" ng-transclude></div>' +
        '</div>',
      replace: true,
    };
  })
 
  angular.module('raceRegistration').directive('pane', function() {
    return {
      require: '^tabs',
      restrict: 'E',
      transclude: true,
      scope: { title: '@', id:'@'},
      link: function(scope, element, attrs, tabsController) {
        tabsController.addPane(scope);
      },
      template:
        '<div class="tab-pane" ng-class="{active: selected}" ng-transclude>' +
        '</div>',
      replace: true
    };
  })