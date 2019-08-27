
// Fix for Selectize
$('#builder-REPLACEME').on('afterCreateRuleInput.queryBuilder', function(e, rule) {
  if (rule.filter.plugin == 'selectize') {
    rule.$el.find('.rule-value-container').css('min-width', '200px')
    .find('.selectize-control').removeClass('form-control');
     }
});

// Fix for Bootstrap Datepicker
$('#builder-REPLACEME').on('afterUpdateRuleValue.queryBuilder', function(e, rule) {
  if (rule.filter.plugin === 'datepicker') {
    rule.$el.find('.rule-value-container input').datepicker('update');
  }
});

$('#builder-REPLACEME').queryBuilder({ plugins: ['bt-tooltip-errors'], rules: rules_REPLACEME, select_placeholder: "--Pick a Field--",
  filters: 
