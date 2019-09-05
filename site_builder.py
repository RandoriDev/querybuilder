import os
import sys
import shutil
import subprocess
import argparse
import json

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

def build_website(api_file, output_dir):
    with open('templates/template-index-start.html', 'r') as e:
        html_str_1 = e.read()
    
    with open('templates/template-index-middle.html', 'r') as e:
        html_str_2 = e.read()
    
    with open('templates/template-index-end.html', 'r') as e: 
        html_str_3 = e.read() 
        
    with open('templates/confidence_filter', 'r') as e:
        con_filt_str = e.read()

    with open('templates/target_temptation_filter', 'r') as e:
        tt_filt_str = e.read()
    
    sect_str = ''
    
    js_sources_string = ''
    
    js_close_string = '\n});'
    
    with open(api_file, 'r') as af:
        datastore = json.load(af)
        
    schemas = datastore['components']['schemas']
    
    for dash_endpoint in sorted(schemas.keys()):
        try:
            filters = []
            schemas[dash_endpoint]['required']
            endpoint = dash_endpoint.replace('-', '_');
            
            append_conf_filt = False
            append_tt_filter = False
            
            
            for k,v in sorted(schemas[dash_endpoint]['properties'].items()):
                if v['type'] == 'object':
                    # Don't process endpoints with an 'object' type (aka Tags).
                    # I have not worked out the javascipt to do a new type.
                    continue

                if k == 'confidence':
                    append_conf_filt = True

                if k == 'target_temptation':
                    append_tt_filter = True
            
                if not k in ['confidence', 'target_temptation', 
                                'deleted', 'tags', 'org_id']:
                    filter_dict = {}

                    filter_dict['id'] = 'table.' + k

                    filter_dict['label'] = ' '.join(
                        map(lambda s: s.capitalize(),k.split('_'))
                        )
    
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
            
            if append_conf_filt:
                filt_string = filt_string.rstrip(']').rstrip('\n') + ',' + \
                                con_filt_str + '\n]'
            
            if append_tt_filter:
                filt_string = filt_string.rstrip(']').rstrip('\n') + ',' + \
                                tt_filt_str + '\n]'
            
            #default rule filename
            drf = 'templates/default_rules/{}.js'.format(endpoint)
            
            with open(drf, 'r') as d :
                def_rules_str = d.read()
            
            with open('templates/template-javascript.js', 'r') as j:
                js_source_code = j.read().rstrip('\n')
            
            js_str = ''.join([def_rules_str, js_source_code, 
                                filt_string, js_close_string])
            
            js_str = js_str.replace('REPLACEME', endpoint)
            
            output_filename = '{}/js/randori/{}.js'.format(output_dir, 
                                                            endpoint)
            
            with open(output_filename, 'w+') as o:
                o.write(js_str)
            
            
            with open('templates/template-index-section.html', 'r') as f:
                sect_str = sect_str + f.read().replace('REPLACEME', endpoint)
            
            js_sources_string = js_sources_string + \
                '<script src="js/randori/{}.js"></script>\n'.format(endpoint)
    
        except KeyError:
            pass
            
    
    full_page = ''.join([html_str_1, sect_str, html_str_2, 
                        js_sources_string, html_str_3])
    
    index_outfile = '{}/index.html'.format(output_dir)

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

    if not args.input:
        print('No Randori API Spec file provided.  \
Rerun the script with -i <randori-api-spec.json>')
    
    api_file = args.input

    if not args.output:
        print('No output directory defined.  \
Rerun the script with -o </output/directory/name>')
        sys.exit(1)

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

