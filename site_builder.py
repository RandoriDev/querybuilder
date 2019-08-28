import json
import shutil
import os
import argparse
import sys
import subprocess

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)

def build_website(api_file, output_dir):
    with open('templates/template-index-start.html', 'r') as s:
        html_start_string = s.read()
    
    section_string = ''
    
    with open('templates/template-index-middle.html', 'r') as m:
        html_middle_string = m.read()
    
    js_sources_string = ''
    
    with open('templates/template-index-end.html', 'r') as e: 
        html_end_string = e.read() 
        
        
    javascript_close_string = '\n});'
    
    confidence_filter_string = """
      {
        id: 'table.confidence',
        label: 'Confidence',
        type: 'integer',
        plugin: 'selectize',
        plugin_config: {
          valueField: 'val',
          labelField: 'name',
          searchField: 'name',
          sortField: 'val',
            create: true,
            maxItems: 1,
            plugins: ['remove_button'],
            onInitialize: function() {
              var that = this;
              $.getJSON('data/confidence-levels.json', function(data) {
                data.forEach(function(item) {
                  that.addOption(item);
                });
              });
            }
          },
          valueSetter: function(rule, value) {
            rule.$el.find('.rule-value-container input')[0].selectize.setValue(value);
          }
      }"""
        
    target_temptation_filter_string = """
      {
        id: 'table.target_temptation',
        label: 'Target Temptation',
        type: 'integer',
        plugin: 'selectize',
        plugin_config: {
          valueField: 'val',
          labelField: 'name',
          searchField: 'name',
          sortField: 'val',
          create: true,
          maxItems: 1,
          plugins: ['remove_button'],
          onInitialize: function() {
            var that = this;
            $.getJSON('data/target-temptation-levels.json', function(data) {
              data.forEach(function(item) {
                that.addOption(item);
              });
            });
          }
        },
        valueSetter: function(rule, value) {
          rule.$el.find('.rule-value-container input')[0].selectize.setValue(value);
        }
      }"""
    
    with open(api_file, 'r') as af:
        datastore = json.load(af)
        
    schemas = datastore['components']['schemas']
    
    for dash_thing in schemas.keys():
        try:
            schemas[dash_thing]['required']
            filters = []
            thing = dash_thing.replace('-', '_');
            
            append_confidence_filter = False
            append_target_temptation_filter = False
            
            
            for k,v in sorted(schemas[dash_thing]['properties'].items()):
                if v['type'] == 'object':
                    # Do not process things with an "object" type (aka Tags)
                    #  Have not worked out the javascipt mechanics to do a new type
                    continue
                if k == 'confidence':
                    append_confidence_filter = True
                if k == 'target_temptation':
                    append_target_temptation_filter = True
            
                if not k in ['confidence', 'target_temptation', 'deleted', 'tags', 'org_id', 'name_type']:
                    filter_dict = {}
                    filter_dict['id'] = 'table.' + k
                    filter_dict['label'] = ' '.join(map(lambda s: s.capitalize(),k.split('_')))
    
                    if v['type'] == 'number':
                        filter_dict['type'] = 'double'
                    else:
                        filter_dict['type'] = v['type']
            
                    if k in ['first_seen', 'last_seen' ]:
                        filter_dict['type'] = 'date'
                        filter_dict['validation'] = {'format': 'MM/DD/YYYY'}
                        filter_dict['plugin'] = 'datepicker'
                        filter_dict['plugin_config'] = { 'format': 'mm/dd/yyyy',  'todayBtn': 'linked', 'todayHighlight': True, 'autoclose': True }
            
                    filters.append(filter_dict)
            
            
            filter_string = json.dumps(filters, indent=2).replace('"','\'')
            
            if append_confidence_filter:
                filter_string = filter_string.rstrip(']').rstrip('\n') + "," + confidence_filter_string + "\n]"
            
            if append_target_temptation_filter:
                filter_string = filter_string.rstrip(']').rstrip('\n') + "," + target_temptation_filter_string + "\n]"
            
            
            default_rule_filename = "templates/default_rules/{}.js".format(thing)
            
            with open(default_rule_filename, 'r') as d :
                default_rules_string = d.read()
            
            with open('templates/template-javascript.js', 'r') as j:
                javascript_source_code = j.read().rstrip('\n')
            
            entire_thing = default_rules_string + javascript_source_code + filter_string + javascript_close_string
            
            entire_thing = entire_thing.replace('REPLACEME', thing)
            
            output_filename = '{}/js/randori/{}.js'.format(output_dir, thing)
            
            with open(output_filename, 'w+') as o:
                o.write(entire_thing)
            
            
            with open('templates/template-index-section.html', 'r') as f:
                section_string = section_string + f.read().replace('REPLACEME', thing)
            
            js_sources_string = js_sources_string + '<script src="js/randori/REPLACEME.js"></script>\n'.replace('REPLACEME', thing)
    
        except KeyError:
            pass
            
    
    
    
    full_page = html_start_string + section_string + html_middle_string + js_sources_string + html_end_string
    
    index_outfile = '{}/index.html'.format(output_dir)

    with open(index_outfile, 'w+') as o:
        o.write(full_page)
        
    print ('Done')
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "")
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument("-i", "--input", required=True, help="File containing the Randori API Spec.")
    required.add_argument("-o", "--output", required=True, help="Directory in which to write the generated files.")
    optional.add_argument("-s", "--setup", default=False, action="store_true",
        help="If the setup arg/flag is provided, copy the contents of the 'framework' directory to the output directory.")
    parser._action_groups.append(optional)

    args = parser.parse_args()

    if not args.input:
        print("No Randori API Spec file provided.  Rerun the script with -i <randori-api-spec.json>")
    
    api_file = args.input

    if not args.output:
        print("No output directory defined.  Rerun the script with -o </output/directory/name>")
        sys.exit(1)

    output_dir = args.output
    if not ( os.path.isdir(output_dir)):
        print ("{} does not exist.  Please create the directory and run the script again.".format(output_dir))
        sys.exit(1)

    if not (os.access(output_dir, os.W_OK) and os.access(output_dir, os.X_OK)):
        print ("{} is not writeable by the current user.  Please change the permissions on the directory and run the script again.".format(output_dir))
        sys.exit(1)


    if args.setup:
        os.chdir('framework')
        copytree('.', output_dir)
        os.chdir('..')
        try:
            subprocess.run(['restorecon', '-r', '/usr/share/nginx/html/randori/'])
        except FileNotFoundError:
            pass

    build_website(api_file, output_dir)
