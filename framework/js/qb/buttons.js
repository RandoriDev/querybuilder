
// reset builder
$('.clear-rules').on('click', function() {
  var target = $(this).data('target');

  $('#builder-'+target).queryBuilder('reset');
});

// set rules
$('.set-json').on('click', function() {
  var target = $(this).data('target');
  var rules = window['rules_'+target];

  $('#builder-'+target).queryBuilder('setRules', rules);
});

// show JSON
$('.show-json').on('click', function() {
  var target = $(this).data('target');
  var result = $('#builder-'+target).queryBuilder('getRules');

  if (!$.isEmptyObject(result)) {
    bootbox.alert({
      title: 'JSON Formatted Query',
      message: '<pre class="code-popup">' + format4popup(result) + '</pre>'
    });
  }
});

//show Base64
$('.show-base64').on('click', function() {
  var target = $(this).data('target');
  var result = $('#builder-'+target).queryBuilder('getRules');

  if (!$.isEmptyObject(result)) {
    bootbox.alert({
      title: "Base64 Encoded Query",
      message: '<pre class="code-popup">' + formatBase64(result) + '</pre>'
    });
  }
});


function format4popup(object) {
  return JSON.stringify(object, null, 2).replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function formatBase64(object) {
  return btoa(JSON.stringify(object, null, 2))
}
