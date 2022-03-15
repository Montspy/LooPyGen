""" START COMMENT SECTION

Consider the lowest number to be your background layer. Then you are adding new layers on top in order.

You must have at least 2 layers to run this script.

Don't change anything that starts with "layer" other than its number.

Increase the number for each line that you add.

Add as many layers as you need.

Make sure to copy the entire layer section when adding new ones.

Only edit the values for "filenames" and "weights".

Increase the layer number by 1 for each new section.

Add as many filenames and weights as needed.
    1. You have to have the same amount of weights as you do filenames.
    2. When you add up all the weights together, they must equal exactly 100.

    What you're doing is setting a "percentage chance this item gets picked"

"layer0X": {
    "layer_name": "Pretty Trait Name 0X",
    "filenames": {
        "Pretty Item Name 01": "item_01.png",
        "Pretty Item Name 02": "item_02.png"
    },
    "weights": [
        50,
        50
    ],
    "names": []
}

END COMMENT SECTION """

## Give the collection a name
COLLECTION_NAME="Collection Title"

layers = {
    1: {
        "layer_name": "Pretty Trait Name 01",
        "filenames": {
            "Pretty Item Name 01": "item_01.png",
            "Pretty Item Name 02": "item_02.png"
        },
        "weights": [
            50,
            50
        ],
        "names": []
    },
    2: {
        "layer_name": "Pretty Trait Name 02",
        "filenames": {
            "Pretty Item Name 01": "item_01.png",
            "Pretty Item Name 02": "item_02.png"
        },
        "weights": [
            50,
            50
        ],
        "names": []
    }
}
