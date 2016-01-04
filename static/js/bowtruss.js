function BowTrussParallax() {
  /**
   * Determine when a specific y position becomes visible in the browser window
   */
  this.calculateDelay = function(posOnDoc) {
    var delay = posOnDoc - $(window).height();
    return delay;
  };

  /**
   * Prevents spaces below a background-image during parallax effect.
   */
  this.calculateStart = function() {
    var windowHeight = $(window).height();

    if (windowHeight >= 850) {
      this.start = 150;
    } else {
      this.start = 0;
    }
  }

  /**
   * Initializes Scrollorama
   */
  this.startParallax = function() {
    var that = this;
    var scrollorama = $.scrollorama({ enablePin: false, blocks: '.parallax' });

    jQuery.each(this.parallaxedElements, function(element, delay) {
      if (element == '#top') {
        scrollorama.animate(element, { delay: delay, duration: that.duration, property: 'background-position-y', start: 0, end: -300 });
      } else {
        scrollorama.animate(element, { delay: delay, duration: that.duration, property: 'background-position-y', start: that.start, end: -150 });
      }
    });
  }

  /**
   * Constructor
   */
  this.initialize = function() {
    this.calculateStart();
    this.startParallax();

    var that = this;

    $(window).resize(function() {
      that.calculateStart();
      that.startParallax();
    });
  }

  this.blockHeight = 850 + 525; // Height of 1 bg image + 1 color block
  this.duration    = 850 * 2; // Duration in pixels for parallax effect
  this.start       = 0; // Starting background-position-y of a bg image

  /**
   * The starting delay of a parallax effect depends on when a particular
   * bg image block is visible in the window (window height varies by
   * resolution).
   */
  this.parallaxedElements = {
    '#top': 0,
    '#bg3': this.calculateDelay(this.blockHeight * 1),
    '#bg5': this.calculateDelay(this.blockHeight * 2),
    '#location': this.calculateDelay(this.blockHeight * 3),
    '#bg9': this.calculateDelay(this.blockHeight * 4),
    '#contact': this.calculateDelay(this.blockHeight * 5),
  }

  this.initialize();
};

/**
 * Initializes scrollTo listeners for header links.
 */
function bowtrussHeader() {
  var button      = $('#bowtruss-header button'); 
  $('div#bowtruss-header ul li a.scrollto').click(function(e) {
    e.preventDefault();

    if ($(this).hasClass('logo')) {
      $.scrollTo(0, 500);

    } else {
      $.scrollTo('#' + $(this).attr('rel'), 500);
       $('.navbar-toggle').click();
    }
  });
}

$(function() {  
    var pull        = $('#pull');  
        menu        = $('#bowtruss-header ul'); 
        button      = $('#bowtruss-header button');  
        menuHeight  = menu.height();  
  
    $(button).on('click', function(e) {  
        e.preventDefault();  
        //alert('button pressed');
        if(menu.is(':hidden')){ 
           menu.show();

        } else {
          
            
        }
    });
    $('.scrollto').on('click', function(e) {  
        var w = $(window).width();
        if(w < 719) {
          menu.slideToggle(function(){
            if(menu.is(':hidden')){ 
              menu.show();
            } else {
              //$('.video-background').children().hide();
            }
          
          });
        }  
    });  
}); 

$(window).resize(function(){  
    var windowsize = $(window).width();  
    if(windowsize > 719 && menu.is(':hidden')) { 
        menu.removeAttr('style');  
    }
    if (windowsize < 1600) {
      var vidheight = windowsize * 0.5625;
      $('div.parallax div.video-background').height(vidheight);
      $('div.parallax div#top').height(vidheight + 45);
    };

});  


$(document).ready(function() {
  console.log('ready');
  var windowsize = $(window).width();  
  if (windowsize < 1600) {
    var vidheight = windowsize * 0.5625;
    $('div.parallax div.video-background').height(vidheight);
    $('div.parallax div#top').height(vidheight + 45);
   };
});

/**
 * Dynamic validations for wholesale inquiry form.
 */
function wholesaleInquiryForm() {
  var wholesaleForm = $('#wholesale-inquiries form.wholesale').validate({
    errorElement: 'p',
    rules: {
      'name': {
        required: true,
      },
      'business_name': {
        required: true,
      },
      'email': {
        email: true,
        required: true,
      },
      'address': {
        required: true,
      },
      'city': {
        required: true,
      },
      'state': {
        required: true,
      },
      'phone': {
        required: true,
      },
      'subject': {
        required: true,
      },
      'message': {
        required: true,
      },
    },
  });
}
