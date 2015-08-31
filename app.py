"""
main flask application for table ui
"""

import json
import jsonpointer as jp
import yaml

from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO
from flask.ext.bower import Bower

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
Bower(app)
socketio = SocketIO(app)


import blaze as bz
import pandas as pd

from bokeh.models.widgets import Panel, Tabs
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.resources import CDN
from bokeh.protocol import serialize_json

# Import interactive blaze data
data = {
    'iris': bz.Data(bz.CSV('static/iris.data.txt')),
    'accounts': bz.Data('static/accounts.json'),
}

# Import some JSON data for JSON pointer example
with open('static/gh.json','r') as f:
    data['github'] = json.load(f)

# Dataframe for Bokeh demo
datademo = bz.odo( data['iris'], pd.DataFrame )
source = ColumnDataSource( datademo )


with open( 'app.yaml') as f:
    config = yaml.load( f, Loader=yaml.BaseLoader )

def keys():
    """
    Return dataframe keys
    """
    #
    return json.dumps( datademo.columns.values.tolist() )

def dataframe_html():
    """
    Return dataframe as an HTML object
    """
    return datademo.to_html()

def bokeh_data():
    """
    Export bokeh json from request.data

    Rows are tabs
    Pane's and rows versus column
    """
    tab = []
    plot_data = json.loads( request.data )

    plt = []
    for tab_name in plot_data:
        figure_data = plot_data[tab_name]
        plt.append( figure(**figure_data['figure']))
        glyphs = figure_data['glyphs']
        for glyph in glyphs:
            tmp = list(glyph.values())[0]
            tmp['source'] = source
            getattr( plt[-1], list(glyph.keys())[0] )(**tmp)
        tab.append( Panel(child=plt[-1],title=tab_name))
    tabs = Tabs(tabs=tab)
    return json.dumps({
        'all_models': serialize_json( tabs.dump() ),
        'ref': tabs.ref,
    })

def show_table():
    global datademo, source
    if request.args.get('data'):
        datademo = pd.read_csv( request.args.get('data') )
    else:
        datademo = bz.odo( data['iris'], pd.DataFrame )

    source = ColumnDataSource( datademo )
    return render_template( 'layout.html')

def show_dataframe( data_key ):
    """
    JSON pointer to access bz.Data
    """
    convert = jp.resolve_pointer(
        data, '/'+ data_key.rstrip('/')
    )

    if data_key.split('/')[0] in ['iris','accounts']:
        # Convert blaze object to html representation
        return bz.odo(
            convert , pd.DataFrame
        ).to_html()
    else:
        # Return YAML string
        return json.dumps(convert)

# Decorate the functions defined in the yaml manifest
routes = config['routes']
for route in routes:
    func_to_decorate = routes[route]
    methods = ['GET']
    if isinstance( func_to_decorate, dict ):
        methods = [s.upper() for s in func_to_decorate['methods']]
        func_to_decorate = func_to_decorate['function']

    method = ['GET']
    for csv in route.split(','):
        print( func_to_decorate )
        app.route( csv,
            methods = methods
        )(
            globals()[func_to_decorate],
        )

# run the app
if __name__ == '__main__':
    socketio.run(app,port=5001)
