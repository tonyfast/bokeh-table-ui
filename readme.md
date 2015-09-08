# The application

* Flask - application
* Jinja/Javascript - Front end
* Blaze - data manipulation
* Bokeh - takes in Blaze and exports Bokeh

# The api

Call python functions and data using a URI schema.

```
# *kwargs
/api/module/method?arg1=/data/dataname&arg=/module2/method2/data/dataname
# *args
/api/module/method?[/data/dataname,/module2/method2/data/dataname]
```

# Sample methods to load

```
multiply: /operator/mul?[/data/iris/sepal_length,10]
setosa: /blaze/like/data/iris?species=[setosa]
real: /pandas/read_csv?filepath_or_buffer=http://www.betfairpromo.com/betfairsp/prices/dwbfpricesukwin07092015.csv
new: /blaze/by/data/iris/species?max=/blaze/max/data/iris/sepal_length
iris: /blaze/transform/data/iris?ratio=/operator/truediv?[/data/iris/sepal_length,/data/iris/sepal_width]
sorted: /blaze/sort?child=/data/iris&key=sepal_length&ascending=No
```
