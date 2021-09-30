import yaml
from textwrap import indent

def populate_api():
    
    f = open('pharus//dynamic_api.py', 'w')
    y = open('pharus//dynamic_api_spec.yaml', 'r')
    
    header_template = """
# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector, dj

"""
    f.write(header_template)

    route_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:
    
{query}

    djconn = _DJConnector._set_datajoint_config(jwt_payload)
    vm_dict = {{s: dj.VirtualModule(s, s, connection=djconn) for s in dj.list_schemas()}}
    query, fetch_args = dj_query(vm_dict)
    return str(query.fetch(**fetch_args))
"""

    valuesYaml = yaml.load(y, Loader=yaml.FullLoader)
    pages = valuesYaml['SciViz']['pages']
    
    # Crawl through the yaml file for the routes in the components
    for grids in pages.values():
        for grid in grids['grids'].values():
            for comp in grid['components'].values():
                f.write(route_template.format(route=comp['route'],
                    method_name=comp['route'].replace('/', ''),
                    query=indent(comp['dj_query'], '    ')))

    f.close()