## Top level image directory, relative to generate.py
topLevel = "./images/source_layers"

"""
This script treats each layer of the image as traits, and each variant of a layer as items.

This section links the code names to the "pretty" names that you want to
appear on websites. Anything that has "layer" or "variant" in the name
should only be incremented. Leave the "layer" or "variant" part as is.

## Tell the script about each folder
layer01dir = topLevel + "/layer01/"
layer02dir = topLevel + "/layer02/"

## Give each trait a name
names = {
    "collection": "Collection Title",
    "layer01": "Pretty Trait Name 01",
    "layer02": "Pretty Trait Name 02"
}

If you were to increase the traits to 4, then it would look like this

## Tell the script about each folder
layer01dir = topLevel + "/layer01/"
layer02dir = topLevel + "/layer02/"
layer02dir = topLevel + "/layer03/"
layer02dir = topLevel + "/layer04/"

## Give each trait a name
names = {
    "collection": "Collection Name",
    "layer01": "Pretty Trait Name 01",
    "layer01": "Pretty Trait Name 02",
    "layer01": "Pretty Trait Name 03",
    "layer02": "Pretty Trait Name 04"
}
"""

## Tell the script about each folder
layer01dir = topLevel + "/layer01/"
layer02dir = topLevel + "/layer02/"

## Give each trait a name
names = {
    "collection": "Collection Title",
    "layer01": "Pretty Trait Name 01",
    "layer02": "Pretty Trait Name 02"
}

"""
Make sure to copy the entire layer section when adding new ones.

layer0X_filenames - Links the "pretty" names to the filenames.

layer0X_weights - Sets the rarity for each item in layer0X_filenames. There must be a weight for each item.
                  When added up, all weights should equal exactly 100.

layer0X_names - Automatically generated from what you enter into layer0X_filenames
"""

## Start Trait 01
layer01_filenames = {
    "Pretty Item Name 01": "item_01.png",
    "Pretty Item Name 02": "item_02.png"
}

layer01_weights = [
    50,
    50
]

layer01_names = list(layer01_filenames.keys())
## End Trait 01

## Start Trait 02
layer02_filenames = {
    "Pretty Item Name 01": "item_01.png",
    "Pretty Item Name 02": "item_02.png"
}

layer02_weights = [
    50,
    50
]

layer02_names = list(layer02_filenames.keys())
## End Trait 02
