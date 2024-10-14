# ETLs

In cupyd, ETLs are DAGs (**D**irected **A**cyclic **G**raphs). They are composed of Nodes that
will generate or process Items (any pickleable Python object) in a specified flux.

## Defining your own ETL

To define an ETL, you first need to define its Nodes and setup their connections, using the rshift
operator (`>>`) between them:

``` py 
ext = IntegerGenerator(10_000)
add = AddOne()
sub = SubtractOne()
ldr = ListLoader()

ext >> add >> sub >> ldr

etl = ETL(ext)
```

Nodes can connect/feed their output into multiple Nodes, in this example we will feed the same
items from the IntegerGenerator onto two different Nodes:

``` py 
ext = IntegerGenerator(10_000)
add = AddOne()
sub = SubtractOne()

ext >> [add, sub]
```

This is called _branching_.

## Run your ETL

You would simply call run(), with the configuration you want.

``` py 
etl.run(workers=8, show_progress=True)
```

### ETL parameters

TODO
