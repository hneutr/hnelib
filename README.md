`hnelib`: a bunch of tools/utilities I use, mostly while doing datascience.

installation: `pip install hnelib`

# hnelib.runner

is the core of my "science" workflow. It helps me organize plots/dataframes/tables and keep things clean.

The main thing here is the `Runner` object. The point of this thing is to separate _doing_ from _saving_, giving you more flexibility to parameterize things that do (scripts/plots/etc) without having to copy those functions around and change where they save to.

You set up a `Runner` like so:

```
from hnelib.runner import Runner

runner = Runner(
    collection={ ... },
    directory= ... # place where you want things to get saved
)
```

You then run something in the collection by calling `runner.run(some string here)`.

A collection is a dictionary that maps to things you want to run. It lets you define a directory structure in your code that will be reproduced when saving things. Usefully though, it lets you call things in a not-so-verbose way.

Here's an example collection:
```
collection = {
    'variable_1': {
        'sub_plot1': {
            'do': plotting_function,
        },
        'sub_plot2': {
            'do': plotting_function,
            'kwargs': {
                'argument': value,
            },
        },
    },
    'variable_2': plotting_function_2,
}
```

I can call `runner.run('v/subplot1')` and it will run the function at
`collection['variable_1']['sub_plot1']['do']`. Alternatively, I could call `runner.run('variable_1')` and it would do the same thing, since `sub_plot1` is a unique `leaf`.


# hnelib.plots

has functions for plotting things.

# hnelib.pandas

has functions for using pandas.
