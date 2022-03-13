## Top level image directory, relative to generate.py
topLevel = "./images/source_layers"

"""
You can add as many traits as you like, you just have to follow this outline on adding new ones.
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

## Traits

## Trait 01
trait01 = ["Trait Item 01","Trait Item 02"]
trait01_weights = [50, 50]

"Trait Item 01","Trait Item 02"

trait01_paths = {
    "Trait Item 01": "trait_item_01.png",
    "Trait Item 02": "trait_item_02.png"
}

## Trait 02
trait02 = ["Trait Item 01","Trait Item 02"]
trait02_weights = [50, 50]

"Trait Item 01","Trait Item 02"

trait02_paths = {
    "Trait Item 01": "trait_item_01.png",
    "Trait Item 02": "trait_item_02.png"
}