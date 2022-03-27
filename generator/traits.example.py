""" START COMMENT SECTION

Consider the lowest number to be your background layer. Then you are adding new layers on top in order.

You must have at least 2 layers to run this script.

Only change the values and layer numbers in the layers dictionary.

Add as many layers as you need, just remember to increase the layer number when copying a new section.

Add as many "filenames" and "weights" as needed.

    1. You have to have the same amount of weights as you do filenames.
    2. When you add up all the weights together, they must equal exactly 100.

    What you're doing is setting a "percentage chance this item gets picked"

An Example of 1 Layer:

{
    "layer_name": "Pretty Trait Name 0X",
    "filenames": {
        "Pretty Item Name 01": "item_01.png",
        "Pretty Item Name 02": "item_02.png"
    },
    "weights": [
        50,
        50
    ]
}

END COMMENT SECTION """

config = {
    ## Uncomment 'animated_format' to choose the format for animated NFTs. Default: .webm
    ## .webm: High quality with alpha, .mp4: High quality without alpha, .gif: Fastest
    # "animated_format": ".gif",
    ## Uncomment 'thumbnails' to generate thumbnails of resolution [width, height]. If only [width] is provided, calculates y based on aspect ratio
    ## thumbnails are used in the 'image' metadata field
    # "thumbnails": [640],
}

## Give the collection a name
COLLECTION_NAME="Collection Name"

## Layers dictionary
layers = [
    {   # Background Color
        "layer_name": "Background Color",
        "rgba": {
            # Uncomment Black for black background
            # "Black":       (  0,   0,   0, 255),
            "Transparent": (  0,   0,   0,   0),
        },
        "weights": [
            100
        ],
        "size": (640, 640)  # Adjust to the size of your images
    },
    {   # layer01
        "layer_name": "Pretty Trait Name 01",
        "filenames": {
            "Pretty Item Name 01": "item_01.png",
            "Pretty Item Name 02": "item_02.png"
        },
        "weights": [
            50,
            50
        ]
    },
    {   # layer02
        "layer_name": "Pretty Trait Name 02",
        "filenames": {
            "Pretty Item Name 01": "item_01.png",
            "Pretty Item Name 02": "item_02.png"
        },
        "weights": [
            50,
            50
        ]
    }
]

def get_variation_cnt():
    cnt = 1
    for l in layers:
        cnt *= len(l["weights"])
    return cnt
