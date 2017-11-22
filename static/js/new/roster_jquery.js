$(function() {
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

 
});