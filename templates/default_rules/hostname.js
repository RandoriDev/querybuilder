var rules_REPLACEME = {
  condition: 'AND',
  rules: [{
    id: 'table.confidence',
    operator: 'greater_or_equal',
    value: 60
  }, {
    condition: 'OR',
    rules: [{
      id: 'table.hostname',
      operator: 'not_ends_with',
      value: 'foo.com'
    }, {
      id: 'table.target_temptation',
      operator: 'greater_or_equal',
      value: 15
    }]
  }]
};

