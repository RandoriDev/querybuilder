import copy
import os
import re
import sys
import shutil
import subprocess
import argparse
import json

assert sys.version_info >= (3, 0), "This script requires the use of Python 3"


hostname_default_rule='''var rules_REPLACEME = {
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
'''


default_rule='''var rules_REPLACEME = {
  condition: "AND",
  rules: [
    {
      id: "table.confidence",
      operator: "greater_or_equal",
      value: 60
    }
  ]
};
'''


ep_wo_confidence_rule='''var rules_REPLACEME = {
  condition: "AND",
  rules: [
    {
      id: "table.id",
      operator: "equal",
      value: "<uuid_here>"
    }
  ]
};
'''






def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or \
            os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def labelize(field_name):

    lbl = ' '.join(map(lambda s: s.capitalize(),field_name.split('_')))

    return lbl


def craft_selectize_string(field_name, picklist_data_type):

    lbl = labelize(field_name, )

    ss = '''  {
    id: 'table.xxxfield_namexxx',
    label: 'xxxlblxxx',
    type: 'xxxdata_typexxx',
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
        xxxfield_namexxx_json.forEach(function(item) {
            that.addOption(item);
          });
      }
    },
    valueSetter: function(rule, value) {
      rule.$el.find('.rule-value-container input')[0].selectize.setValue(value);
    }
  }'''.replace('xxxfield_namexxx', field_name).replace('xxxlblxxx', lbl).replace('xxxdata_typexxx', picklist_data_type)


    return ss


def build_website(api_file, output_dir):
    with open('templates/template-index-start.html', 'r') as e:
        html_str_1 = e.read()
    
    with open('templates/template-index-middle.html', 'r') as e:
        html_str_2 = e.read()
    
    with open('templates/template-index-end.html', 'r') as e: 
        html_str_3 = e.read() 
        
    sect_str = ''
    
    js_sources_string = ''
    
    with open(api_file, 'r') as af:
        datastore = json.load(af)
        
    schemas = datastore['components']['schemas']
    
    do_not_includes = ['querybuilder_rule_group_schema', 'querybuilder_rule_group_schema_2',
                       'querybuilder_rule_group_schema_3', 'querybuilder_rule_group_schema_4',
                       'querybuilder_rule_schema', 'saved_views_model_custom_in', 
                       'saved_views_patch_in']

    for dash_endpoint in sorted(schemas.keys()):

        try:

            filters = []

            schemas[dash_endpoint]['required']

            endpoint = dash_endpoint.replace('-', '_');

            if endpoint in do_not_includes:

                continue
            
            sort_list = []

            specials = {
                'confidence': [ 'integer',
                                { "name": "Min", "val": 0 },
                                { "name": "Low", "val": 25 },
                                { "name": "Medium", "val":60 },
                                { "name": "High", "val": 75 },
                                { "name": "Extreme", "val": 90 },
                                { "name": "Max", "val": 100 }
                ],
                'name_type': [ 'integer',
                                { "name": "Domain Name", "val": 0 },
                                { "name": "Hostname", "val": 1 }
                ],
                'priority_score': [ 'double',
                                    { "name": "Low", "val": 0 },
                                    { "name": "Medium", "val": 20 },
                                    { "name": "High", "val": 29.98 }
                ],
                'target_temptation': [ 'integer',
                                        { "name": "Low", "val": 0},
                                        { "name": "Medium", "val": 15},
                                        { "name": "High", "val": 30},
                                        { "name": "Critical", "val": 40}
                ]
            }

            for k,v in sorted(schemas[dash_endpoint]['properties'].items()):
                
                # skip deleted because it is not cust facing
                # skip all_ports because it is an array and jquery Querybuilder does not support array types
                if k in ['deleted', 'all_ports']:

                    continue

                sort_list.append(f'<nobr>{k}, -{k}</nobr>')

                try:

                    enum_values = v['enum']

                    ev_list = [v['type']]

                    for ev in enum_values:

                        ev_list.append({"name": ev, "val": ev})

                    specials[k] = ev_list

                except KeyError:

                    pass

                        

                if k in specials.keys():

                    filters.append(k)

                    continue
                    
                filter_dict = {}
                
                filter_dict['id'] = f'table.{k}'
                
                filter_dict['label'] = labelize(k)
                
                if v['type'] == 'number':
                    filter_dict['type'] = 'double'
                else:
                    filter_dict['type'] = v['type']
        
                if k in ['first_seen', 'last_seen' ]:
                    filter_dict['type'] = 'date'
                    filter_dict['validation'] = {'format': 'MM/DD/YYYY'}
                    filter_dict['plugin'] = 'datepicker'
                    filter_dict['plugin_config'] = { 
                                                'format': 'mm/dd/yyyy', 
                                                'todayBtn': 'linked', 
                                                'todayHighlight': True, 
                                                'autoclose': True }
        
                filters.append(filter_dict)
            
            
            filt_string = json.dumps(filters, indent=2).replace('"','\'')

            picklist_str = '\n'

            for special, sv in specials.items():

                picklist_data_type = sv.pop(0)

                picklist_str += f'var {special}_json = {json.dumps(sv, indent=2)};\n\n'

                new_str = craft_selectize_string(special, picklist_data_type)

                foo = f"  '{special}'"

                tmpstr = re.sub(foo, new_str, filt_string)

                filt_string = copy.deepcopy(tmpstr)
            
            if endpoint == 'hostname':

                def_rules_str = hostname_default_rule

            elif endpoint in ['artifact', 'detection', 'saved_views']:

                def_rules_str = ep_wo_confidence_rule

            else:

                def_rules_str = default_rule

            
            with open('templates/template-javascript.js', 'r') as j:
                js_source_code = j.read().rstrip('\n')
            
            js_str = ''.join([picklist_str, def_rules_str, js_source_code, 
                                filt_string, '\n});'])
            
            js_str = js_str.replace('REPLACEME', endpoint)
            
            output_filename = f'{output_dir}/js/randori/{endpoint}.js'
            
            with open(output_filename, 'w+') as o:
                o.write(js_str)
            
            sort_str = ', '.join(sort_list)

            sort_str = f'{sort_str}\n<section>\n'

            with open('templates/template-index-section.html', 'r') as f:
                sect_str = sect_str + f.read().replace('REPLACEME', endpoint)
                sect_str = sect_str + sort_str
            
            js_sources_string = js_sources_string + \
                '<script src="js/randori/{}.js"></script>\n'.format(endpoint)

        except KeyError:
            pass
            
    
    full_page = ''.join([html_str_1, sect_str, html_str_2, 
                        js_sources_string, html_str_3])
    
    index_outfile = f'{output_dir}/index.html'

    with open(index_outfile, 'w+') as o:
        o.write(full_page)
        
    print ('Done')
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = '')

    optional = parser._action_groups.pop()

    required = parser.add_argument_group('required arguments')

    required.add_argument('-i', '--input', 
                    required=True, 
                    help='File containing the Randori API Spec.')

    required.add_argument('-o', '--output', 
                    required=True, 
                    help='Directory in which to write the generated files.')

    optional.add_argument('-s', '--setup', default=False, action='store_true',
                            help='If the setup arg/flag is provided, copy the\
                            contents of the "framework" directory to the\
                            output directory.')

    parser._action_groups.append(optional)

    args = parser.parse_args()

    api_file = args.input

    output_dir = args.output

    if not ( os.path.isdir(output_dir)):
        print ('{} does not exist.  Please create the directory and \
run the script again.'.format(output_dir))
        sys.exit(1)

    if not (os.access(output_dir, os.W_OK) and os.access(output_dir, os.X_OK)):
        print ('{} is not writeable by the current user.  \
Please change the permissions on the directory \
and run the script again.'.format(output_dir))
        sys.exit(1)


    if args.setup:
        os.chdir('framework')
        copytree('.', output_dir)
        os.chdir('..')

        if os.path.isfile('/etc/selinux/config'):
            with open('/etc/selinux/config', 'r') as sel:
                if 'SELINUX=enforcing' in sel.read():
                    try:
                        subprocess.run(['restorecon', '-r', output_dir])
                    except FileNotFoundError:
                        pass

    build_website(api_file, output_dir)

