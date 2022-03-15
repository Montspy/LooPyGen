## Top level image directory, relative to generate.py
topLevel = "./images/source_layers"

"""
This scrip treats traits like folders, and items like file names.

This section links the code names to the "pretty" names that you want to
appear on websites. Do not change the "trait0X" names other than increasing
the numbers. Only change the pretty names.

You can add as many traits as you like, you just need to copy the previous
number to a new line, then make sure to increment to the next number.

## Tell the script about each folder
trait01dir = topLevel + "/trait01/"
trait02dir = topLevel + "/trait02/"

## Give each trait a name
names = {
    "collection": "Collection Title",
    "trait01": "Unique Name 01",
    "trait02": "Unique Name 02"
}

If you were to increase the traits to 4, then it would look like this

## Tell the script about each folder
trait01dir = topLevel + "/trait01/"
trait02dir = topLevel + "/trait02/"
trait02dir = topLevel + "/trait03/"
trait02dir = topLevel + "/trait04/"

## Give each trait a name
names = {
    "collection": "Collection Title",
    "trait01": "Unique Name 01",
    "trait01": "Unique Name 02",
    "trait01": "Unique Name 03",
    "trait02": "Unique Name 04"
}
"""

## Tell the script about each folder
trait01dir = topLevel + "/trait01/"
trait02dir = topLevel + "/trait02/"

## Give each trait a name
names = {
    "collection": "Collection Title",
    "trait01": "Unique Name 01",
    "trait02": "Unique Name 02"
}

"""
Make sure to copy the entire trait section for each new trait.
"""

## Traits

## Start Trait 01
trait01 = ["Trait Item 01","Trait Item 02"]
trait01_weights = [50, 50]

trait01_paths = {
    "Trait Item 01": "trait_item_01.png",
    "Trait Item 02": "trait_item_02.png"
}
## End Trait 01

## Start Trait 02
trait02 = ["Trait Item 01","Trait Item 02"]
trait02_weights = [50, 50]

trait02_paths = {
    "Trait Item 01": "trait_item_01.png",
    "Trait Item 02": "trait_item_02.png"
}
## End Trait 02
