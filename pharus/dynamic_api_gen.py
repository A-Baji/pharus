from textwrap import indent
from pathlib import Path
import os
import yaml
import pkg_resources


def populate_api():
    header_template = """# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector, dj
from flask import request
from json import loads
from base64 import b64decode
import inspect
"""
    route_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            djdict['query'] = djdict['query'] & restriction()
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                query=djdict['query'], fetch_args=djdict['fetch_args'],
                **{{k: (int(v) if k in ('limit', 'page')
                   else (v.split(',') if k == 'order'
                   else loads(b64decode(v.encode('utf-8')).decode('utf-8'))))
                   for k, v in request.args.items()}},
                )
            return dict(recordHeader=record_header, records=table_tuples,
                        totalCount=total_count)
        except Exception as e:
            return str(e), 500


@app.route('{route}/attributes', methods=['GET'])
@protected_route
def {method_name}_attributes(jwt_payload: dict) -> dict:

{query}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            attributes_meta = _DJConnector._get_attributes(djdict['query'])

            return dict(attributeHeaders=attributes_meta['attribute_headers'],
                        attributes=attributes_meta['attributes'])
        except Exception as e:
            return str(e), 500
"""

    plot_route_template = '''

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            djdict['query'] = djdict['query'] & restriction()
            djdict['query'] = djdict['query'] & request.args
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                fetch_args=djdict['fetch_args'], query=djdict['query'], fetch_blobs=True)
            return dict(table_tuples[0][0])
        except Exception as e:
            return str(e), 500
'''

    metadata_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            djdict['query'] = djdict['query'] & restriction()
            djdict['query'] = djdict['query'] & request.args
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                fetch_args=djdict['fetch_args'], query=djdict['query'])
            return dict(recordHeader=record_header, records=table_tuples,
                        totalCount=total_count)
        except Exception as e:
            return str(e), 500
"""

    pharus_root = f"{pkg_resources.get_distribution('pharus').module_path}/pharus"
    api_path = f'{pharus_root}/dynamic_api.py'
    spec_path = os.environ.get('API_SPEC_PATH')

    with open(Path(api_path), 'w') as f, open(Path(spec_path), 'r') as y:
        f.write(header_template)
        values_yaml = yaml.load(y, Loader=yaml.FullLoader)
        pages = values_yaml['SciViz']['pages']

        # Crawl through the yaml file for the routes in the components
        for page in pages.values():
            for grid in page['grids'].values():
                if grid['type'] == 'dynamic':
                    f.write(route_template.format(route=grid['route'],
                            method_name=grid['route'].replace('/', ''),
                            query=indent(grid['dj_query'], '    '),
                            restriction=indent(grid['restriction'], '    ')))
                    for comp in grid['component_templates'].values():
                        if comp['type'] == 'plot:plotly:stored_json':
                            f.write(plot_route_template.format(route=comp['route'],
                                    method_name=comp['route'].replace('/', ''),
                                    query=indent(comp['dj_query'], '    '),
                                    restriction=indent(comp['restriction'], '    ')))
                        if comp['type'] == 'metadata':
                            f.write(metadata_template.format(route=comp['route'],
                                    method_name=comp['route'].replace('/', ''),
                                    query=indent(comp['dj_query'], '    '),
                                    restriction=indent(comp['restriction'], '    ')))
                    continue
                for comp in grid['components'].values():
                    if comp['type'] == 'table':
                        f.write(route_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
                    if comp['type'] == 'plot:plotly:stored_json':
                        f.write(plot_route_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
                    if comp['type'] == 'metadata':
                        f.write(metadata_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
