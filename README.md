# Automatic Randori Querybuilder Website Generator

This repo is intended to be an easy to use tool to generate a self-contained web page that can be used to generate queries for use with the Randori API.

The web page, CSS files and JavaScript files are all either contained in the repo or generated when the python script is run.

The one file that is needed, but not provided in the repo is the API specification file [randori-api.json](https://alpha.randori.io/openapi) (must be authenticated to access).

## Useage
```
usage: site_builder.py [-h] -i INPUT -o OUTPUT [-s]

required arguments:
  -i INPUT, --input INPUT
                        File containing the Randori API Spec.
  -o OUTPUT, --output OUTPUT
                        Directory in which to write the generated files.

optional arguments:
  -h, --help            show this help message and exit
  -s, --setup           If the setup arg/flag is provided, copy the contents
                        of the 'framework' directory to the output directory.
```



