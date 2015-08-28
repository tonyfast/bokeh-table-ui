# Highlights

* yaml manifest for flask routes
* interactive table editor for ColumnDataSources
* simple blaze expressions
* jsonpointer examples on blaze datasources and json sources

# The Data

Blaze Data sources
Bokeh Columns Data Sources

# The Application

http://localhost:5001/
http://localhost:5001/?data=http://samplecsvs.s3.amazonaws.com/Sacramentorealestatetransactions.csv


## Flask Bits

 ``app.yaml`` describes the routes for the apps.  The yaml structure is

```yaml
routes:
  '/,index.html'/:
    function: hello
    methods: [get]
```

is equivalent to

```python
@app.route( '/', methods=['GET'])
@app.route( '/index.html', methods=['GET'])
def hello():
  return "hello"
```

## Bokeh Bits

If a DataFrame is loaded into Bokeh for a visualization, what interactions can
happen to interactively explore the data.

### Table UI

http://localhost:5001/data/github/10/files/
