#import  ipdb; ipdb.set_trace()
"""
main flask application for table ui
"""
from __future__ import division
import os

from flask import Flask, render_template, request, jsonify
from flask.ext.socketio import SocketIO
from flask.ext.bower import Bower

import yaml
import json

import operator

import urllib
import urlparse

import blaze as blaze
import pandas as pandas

from bokeh.models.widgets import Panel, Tabs
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.resources import CDN
from bokeh.protocol import serialize_json

from bokeh.sampledata import iris
iris = blaze.Data(iris.flowers)

data = {
    'iris' : iris,
}
# 'dl': blaze.Data( './downloads.csv')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
bower = Bower(app)
socketio = SocketIO(app)

@app.route('/')
@app.route('/app')
@app.route('/app/<key>')
def hello(key='iris'):
    global data
    return render_template( 'layout.html',
        name= key,
        datasets = data.keys(),
        table_html = table(key),
        columns = cols(key)[1]
    )

def to_df(d):
    print('dd', d)
    return blaze.odo( d, pandas.DataFrame )

@app.route('/table/<key>')
def table( key ):
    """
    Return an html table of the data
    """
    global data
    d = data[key]
    return to_df( d.head() ).to_html()

@app.route('/create/<key>/<path:url>', methods=['GET','POST'])
def create( key,url ):
    """
    Create a new blaze object
    Place the url in the query string
    """
    global data
    data[key] = blaze.Data( blaze.odo( pyapi( data, url + "?" + request.query_string ), pandas.DataFrame )  )

@app.route('/cols/<key>')
def cols( key, operation=None ):
    """
    Return columns and their dshape as json
    """
    global data
    _data = data[key]

    rows, columns = _data.dshape.parameters

    if 'val' in rows:
        row = rows.val
    else:
        row  = '*'

    return row, [{
        'name': col[0],
        'format' : col[1].__str__().lstrip('?')
    } for col in columns.parameters[0] ]

@app.route('/bokeh', methods=['GET','POST'])
def bokeh_data():
    """
    Export bokeh json from request.data
    Rows are tabs
    Pane's and rows versus column
    """
    global data

    tab = []
    plot_data = json.loads( request.data )
    source =  ColumnDataSource( blaze.odo( data[plot_data['dataset_name']], pandas.DataFrame ) )
    plt = []

    for tab_name in plot_data:
        if tab_name != 'dataset_name':
            print(tab_name)
            #import ipdb; ipdb.set_trace()
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

@app.route('/api/<path:api_url>')
def apirouter(  api_url ):
    """
    Trigger apps api to load datasets
    """
    global data
    # import ipdb; ipdb.set_trace( )
    obj = pyapi( data, api_url + "?" + request.query_string )
    return to_df(obj).to_html()

def get_pointer( d, p):
    """
    Get the pointer to a dataset or object
    """
    p = p.strip('/')
    attr = p
    if '/' in p:
        attr, p = p.split('/',1)
        if attr.startswith('_'):
            d = getattr( d, attr.lstrip('_') )
        else:
            d = d[attr]
        return get_pointer( d, p )
    else:
        if attr.startswith('_'):
            d = getattr( d, attr.lstrip('_') )
        else:
            d = d[attr]
        return d

def qs_parser( qs ):
    """
    Convert the query strings
    """
    args, kwargs = [],{}
    if qs:
        qs = urllib.unquote_plus( qs )
        if not '=' in qs:
            args = yaml.load( qs, Loader=yaml.SafeLoader)
            if isinstance(args, str):
                args = [args]
        else:
            for el in qs.split('&'):
                key,value = el.split('=')
                value = yaml.load( value, Loader=yaml.SafeLoader )
                if key in ['kwargs']:
                    kwargs = value
                elif key in ['args']:
                    args = value
                else:
                    kwargs[key] = value

    return args, kwargs

def resolve_args( workspace, args, kwargs ):
    """
    Push args through the api
    """
    if args:
        for index,value in enumerate(args):
            if isinstance( args[index], str) and args[index].startswith('/'):
                prev = args[index]
                args[index] = pyapi( workspace, value.lstrip('/') )
    if kwargs:
        for key in kwargs:
            value = kwargs[key]
            if isinstance( value, str) and value.startswith('/'):
                kwargs[key] = pyapi( workspace, value.lstrip('/') )
    return args, kwargs

def pyapi( workspace, api_url ):
    """
    """
    qs = ''
    if '?' in api_url:
        api_url, qs = api_url.split('?',1)

    args, kwargs = qs_parser( qs )
    args, kwargs = resolve_args( workspace, args, kwargs )
    print('args',args,kwargs)


    module, cmd = api_url.strip('/').split('/',1)

    if module == 'data':
        module = workspace
        endpoint = get_pointer( module, '/' + cmd )
    else:

        module = __import__( module )
        method = cmd
        if '/' in cmd:
            # Execute chained methods
            method, cmd = method.split('/',1)
            endpoint = getattr( module, method )
            endpoint = endpoint( pyapi( workspace, cmd ), **kwargs )
        else:
            endpoint = getattr( module, cmd )
            if kwargs:
                endpoint = endpoint( **kwargs )
            elif args:
                # Array in query string
                endpoint = endpoint( *args )

    return endpoint


# run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
