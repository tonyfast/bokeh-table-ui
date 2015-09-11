from app import workspace

import yaml
import pandas as pd
import blaze as blaze
import operator

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show
from bokeh.resources import INLINE, CDN
import bokeh

import io


class CIOLoader(yaml.Loader):
    pass

def uri_to_value( obj, uri ):
    """
    path to resolve in yaml manifests

    data['foo'].bar  - /foo/_bar
    """
    key = uri.lstrip('/')
    if '/' in uri:
        key,uri = uri.split('/',1)
    else:
        uri = None

    if key.startswith( '_' ):
        obj = getattr( obj, key[1:] )
    else:
        obj = obj[ key ]

    if not uri:
        return obj
    else:
        return uri_to_value( obj, uri )

def yaml_to_args( obj ):
    """
    convert list and dict to list of key and value
    """
    if isinstance( obj, list ):
        args = []
        for arg in obj:
            for key in arg:
                args.append((key,arg[key]))
        return args
    elif isinstance( obj, dict ):
        return [(key, obj[key]) for key in obj ]
    else:
        return obj

def resolve_pointer( workspace, obj ):
    """
    """
    if isinstance( obj, list ):
        for index, value in enumerate(obj):
            if hasattr( value, 'decode'):
                value = value.decode('utf-8')
            if isinstance( value, str ) and value.startswith('/'):
                obj[index] = uri_to_value( workspace, value.lstrip('/') )
            else:
                obj[index] = resolve_pointer( workspace, value )
    elif isinstance( obj, dict ):
        for key in obj:
            value = obj[key]
            if hasattr( value, 'decode'):
                value = value.decode('utf-8')

            if isinstance( value, str ) and value.startswith('/'):
                obj[key] = uri_to_value( workspace, value.lstrip('/') )
            else:
                obj[key] = resolve_pointer( workspace, value )
    return obj

def blaze_constructor(loader, node):
    """
    Execute blaze expression
    """
    global workspace
    obj = loader.construct_mapping(node, deep=True)
    obj = resolve_pointer( workspace, obj )
    blaze_method, args = yaml_to_args( obj )[0]

    if blaze_method == 'odo':
        args[1] = type( args[1] )

    if isinstance( args[-1], dict ):
        # If kwargs are provided
        return getattr( blaze, blaze_method )( *args[:-1], **args[-1])
    # evaluate args
    return getattr( blaze, blaze_method)( *args )

def compute_constructor(loader, node):
    """
    Add a compute operation to a blaze constructor
    """
    return blaze.compute( blaze_constructor(loader, node) )


CIOLoader.add_constructor("!blaze", blaze_constructor)
CIOLoader.add_constructor("!compute", compute_constructor)

def operator_constructor(loader, node):
    """
    Compute operations using built operator module
    """
    global workspace
    obj = loader.construct_mapping(node, deep=True)
    obj = resolve_pointer( workspace, obj )
    operation, arg = yaml_to_args( obj )[0]
    return getattr( operator, operation )( *arg )

CIOLoader.add_constructor("!operator", operator_constructor)

def resolve_constructor(loader, node):
    """
    Resolve the value of an object with path constructors
    """
    global workspace
    arg = loader.construct_mapping(node, deep=True)
    return resolve_pointer( workspace, arg )

CIOLoader.add_constructor("!resolve", resolve_constructor)

def bokeh_constructor( loader, node ):
    """
    build a bokeh plot
    """
    global workspace
    args = loader.construct_mapping(node, deep=True)
    args = resolve_pointer( workspace, args )

    source = None

    if not 'figure' in args:
        args['figure'] = {}

    args['figure'] = resolve_pointer( workspace, args['figure'] )
    if 'source' in args:
        source = blaze.odo( args['source'], ColumnDataSource )

    p = figure( **args['figure'] )

    for glyph, kwargs in yaml_to_args(args['glyphs']):
        if source:
            kwargs['source'] = source
        getattr( p, glyph )( **kwargs )

    return p

CIOLoader.add_constructor("!bokeh", bokeh_constructor)

def widget_constructor( loader, node ):
    """
    Append bokeh widgets
    """
    global workspace
    obj = loader.construct_mapping(node, deep=True)
    obj = resolve_pointer( workspace, obj )
    operation, arg = yaml_to_args( obj )[0]
    if isinstance( arg[-1], dict ):
        # If kwargs are provided
        return getattr( bokeh.models.widgets, operation )( *arg[:-1], **arg[-1])
    return getattr( bokeh.models.widgets, operation )( *arg )

CIOLoader.add_constructor("!widgets", widget_constructor)

def io_constructor( loader, node ):
    """
    Append bokeh widgets
    """
    global workspace
    obj = loader.construct_mapping(node, deep=True)
    obj = resolve_pointer( workspace, obj )
    operation, arg = yaml_to_args( obj )[0]
    if isinstance( arg[-1], dict ):
        # If kwargs are provided
        return getattr( bokeh.io, operation )( *arg[:-1], **arg[-1])
    return getattr( bokeh.io, operation )( *arg )

CIOLoader.add_constructor("!io", io_constructor)

def parse_blaze_manifest_with_loader( filename ):
    global workspace
    if filename.startswith('---'):
        for block in filename.lstrip('---').split('---'):
            workspace = parse_blaze_manifest_with_loader( block )
    else:
        stream = yaml.load( filename, Loader=CIOLoader )
        for key in stream:
            value = stream[key]
            workspace[key] = value
    return workspace

def parse_bokeh_manifest_with_loader(  filename ):
    global workspace
    if filename.startswith('---'):
        tabs = []
        for block in filename.lstrip('---').split('---'):
            print(block,tabs)
            tabs.append( parse_bokeh_manifest_with_loader( block ) )

        return bokeh.models.widgets.Tabs( tabs = tabs )
    else:
        return yaml.load( filename, Loader=CIOLoader )


def __init__():
    pass
