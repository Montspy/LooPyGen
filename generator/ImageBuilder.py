
from os import path
from functools import lru_cache, singledispatchmethod
from PIL import Image
from typing import List, Tuple

class ImageAction(object):
    def __init__(self, func, src: Image.Image):
        self.func = func
        self.img = src

# Represents an image in memory
# Able to overlay other images 
# Able to "queue" overlaying images to reduce io overhead
# Build the image only when requested
class ImageBuilder(object):
    MODE = 'RGBA'
    FFMPEG_EXT = ['gif', 'mp4']
    img: Image.Image
    actions: list[ImageAction]  # Queue of actions required to build the image

    def __init__(self):
        self.reset()

    def reset(self):
        self.img = None
        self.actions = []

    @singledispatchmethod
    def overlay_image(self, src, **kwds):
        raise NotImplementedError(f"Cannot overlay type: {type(src)}")

    @overlay_image.register
    def _(self, fp: str, **kwds):   # From file path
        # print(f"overlay_image for file path {fp}")
        assert path.splitext(fp)[1] not in self.FFMPEG_EXT
        src = self._get_image(fp)

        self.actions.append(ImageAction(Image.alpha_composite, src))

    @overlay_image.register
    def _(self, src: Image.Image, **kwds):   # From PIL.Image
        # print(f"overlay_image for Image {src}")
        self.actions.append(ImageAction(Image.alpha_composite, src))

    @overlay_image.register
    def _(self, rgba: tuple, size: Tuple[int], **kwds):   # From RGBA
        # print(f"overlay_image for rgba {rgba}, size {size}")
        assert len(rgba) == 4
        src = Image.new(mode="RGBA", size=size, color=rgba)
        self.actions.append(ImageAction(Image.alpha_composite, src))

    # Build and return the image
    def build(self) -> Image.Image:
        assert len(self.actions) > 0

        # Make canvas
        if self.img is None:
            self._make_canvas(self.actions[0].img)

        for action in self.actions:
            self.img = action.func(self.img, action.img)

        return self.img

    # Make new canvas
    @singledispatchmethod
    def _make_canvas(self, src) -> None:
        raise NotImplementedError(f"Cannot make canvas from type: {type(src)}")

    @_make_canvas.register
    def _(self, src: Image.Image) -> None:
        assert self.img is None
        self.img = Image.new(mode=self.MODE, size=self._get_size(src))

    # Cached function to get images from 
    @lru_cache
    def _get_image(self, fp: str) -> Image.Image:
        return Image.open(fp).convert('RGBA')

    # Size getters
    @singledispatchmethod
    def _get_size(self, img) -> tuple[int]:
        raise NotImplementedError(f"Cannot get size of type: {type(img)}")

    @_get_size.register
    def _(self, img: Image.Image) -> tuple[int]:
        return img.size
