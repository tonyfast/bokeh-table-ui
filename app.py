from loader import *

from flask import Flask, render_template, request, jsonify, url_for
from flask.ext.bower import Bower

from bokeh.protocol import serialize_json

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
bower = Bower(app)

workspace = {}

@app.route('/')
def hello_world():
    return render_template( 'index.html' )

@app.route('/blaze', methods=['POST'])
def blaze_to_data():
    global workspace
    workspace = parse_blaze_manifest_with_loader( request.data.decode('utf-8') )
    return jsonify(
        keys = list( workspace.keys() ),
    )

@app.route('/bokeh', methods=['POST'])
def bokeh_to_data():
    bk_plot = parse_bokeh_manifest_with_loader( request.data.decode('utf-8') )
    print(bk_plot)
    return jsonify(
        all_models = serialize_json( bk_plot.dump() ),
        ref = bk_plot.ref,
    )


# run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run( port=port)
