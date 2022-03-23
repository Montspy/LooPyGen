
from os import path
from functools import lru_cache, singledispatchmethod
from PIL import Image
from typing import IO, List, Tuple
import tempfile
import subprocess

# Type of image (png, jpg = STATIC - gif, mp4 = DYNAMIC)
class ImageType():
    STATIC = 0
    DYNAMIC = 1

# TODO: split in 2: Static/Dynamic
class ImageDescriptor(object):
    type: ImageType     # Type of image
    img: Image.Image    # static image in memory
    fp: str             # image's filepath on the filesystem

    def __init__(self, type: ImageType, img: Image.Image=None, fp: str=None):
        self.type = type
        self.img = img
        self.fp = fp

# Represents an image in memory
# Able to overlay other images 
# Able to "queue" overlaying images to reduce io overhead
# Build the image only when requested
class ImageBuilder(object):
    STATIC_MODE = 'RGBA'
    FFMPEG_PARAMS = {
        '.gif': {
            'ext': '.gif',
            'cmd': 'ffmpeg -y -i {src1} {ig1} -i {src2} {ig2} -filter_complex [0][1]overlay=format=auto:shortest={shortest},split[s0][s1];[s0]palettegen=reserve_transparent=1[p];[s1][p]paletteuse {out}'
        },
        # '.mp4': {
        #     'ext': '.mp4',
        #     'cmd': None
        # }
    }
    FFMPEG_EXT = list(FFMPEG_PARAMS.keys())

    STATIC_EXT = '.png'
    FFMPEG_MODE = '.gif'
    img: ImageDescriptor                # Final result
    descriptors: list[ImageDescriptor]  # Queue of images required to build the final image
    temp_dir: tempfile.TemporaryDirectory

    def __init__(self):
        self.reset()

    def reset(self):
        self.img = None
        self.descriptors = []

   # Context management for temp files
    def __enter__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, *exc_info):
        self.temp_dir.__exit__(*exc_info)

    @singledispatchmethod
    def overlay_image(self, src, **kwds):
        raise NotImplementedError(f"Cannot overlay type: {type(src)}")

    @overlay_image.register
    def _(self, fp: str, **kwds):   # From file path
        print(f"overlay_image for file path {fp} ({path.splitext(fp)[1]})")
        if path.splitext(fp)[1] in self.FFMPEG_EXT:
            desc = ImageDescriptor(type=ImageType.DYNAMIC, fp=fp)
        else:
            desc = ImageDescriptor(type=ImageType.STATIC, img=self._get_image(fp), fp=fp)
        self.descriptors.append(desc)

    @overlay_image.register
    def _(self, src: Image.Image, **kwds):   # From PIL.Image
        # print(f"overlay_image for Image {src}")
        desc = ImageDescriptor(type=ImageType.STATIC, img=src)
        self.descriptors.append(desc)

    @overlay_image.register
    def _(self, rgba: tuple, size: Tuple[int], **kwds):   # From RGBA
        # print(f"overlay_image for rgba {rgba}, size {size}")
        assert len(rgba) == 4
        src = Image.new(mode="RGBA", size=size, color=rgba)
        desc = ImageDescriptor(type=ImageType.STATIC, img=src)
        self.descriptors.append(desc)

    # Build and return the image
    def build(self) -> ImageDescriptor:
        assert len(self.descriptors) > 0

        # Make canvas
        if self.descriptors[0].type == ImageType.STATIC:
            self._make_canvas(self.descriptors[0].img)
        elif self.descriptors[0].type == ImageType.DYNAMIC:
            self._make_canvas(self.descriptors[0].fp)

        for desc in self.descriptors:
            self.img = self.composite(self.img, desc)

        return self.img

    # Make new canvas
    @singledispatchmethod
    def _make_canvas(self, src) -> None:
        raise NotImplementedError(f"Cannot make canvas from type: {type(src)}")

    @_make_canvas.register
    def _(self, src: Image.Image) -> None:
        assert self.img is None
        self.img = ImageDescriptor(type=ImageType.STATIC, img=Image.new(mode=self.STATIC_MODE, size=self._get_size(src)))

    @_make_canvas.register
    def _(self, fp: str) -> None:
        assert self.img is None
        self.img = ImageDescriptor(type=ImageType.STATIC, img=Image.new(mode=self.STATIC_MODE, size=self._get_size(fp)))

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

    @_get_size.register
    def _(self, desc: ImageDescriptor) -> tuple[int]:
        if desc.type == ImageType.STATIC:
            return desc.img.size
        elif desc.type == ImageType.DYNAMIC:
            cmd = 'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 {desc.fp}'
            return tuple(subprocess.run(cmd, capture_output=True).stdout.split(sep=','))

    # Compositers
    def composite(self, img1: ImageDescriptor, img2: ImageDescriptor) -> ImageDescriptor:
        if img1.type == ImageType.STATIC and img2.type == ImageType.STATIC:
            print('STATIC-STATIC')
            return ImageDescriptor(type=ImageType.STATIC, img=Image.alpha_composite(img1.img, img2.img))
        elif img1.type == ImageType.STATIC and img2.type == ImageType.DYNAMIC:
            print('STATIC-DYNAMIC')
            # Use ffmpeg
            return self._composite_dynamic(img1, img2)
        elif img1.type == ImageType.DYNAMIC and img2.type == ImageType.STATIC:
            print('DYNAMIC-STATIC')
            # Use ffmpeg
            return self._composite_dynamic(img1, img2)
        elif img1.type == ImageType.DYNAMIC and img2.type == ImageType.DYNAMIC:
            print('DYNAMIC-DYNAMIC')
            # Use ffmpeg
            return self._composite_dynamic(img1, img2)

    # Composite 2 dynamic images according to FFMPEG_MODE
    def _composite_dynamic(self, img1: ImageDescriptor, img2: ImageDescriptor) -> ImageDescriptor:
        if img1.fp is None:
            self._get_temp_filepath(img1)
        if img2.fp is None:
            self._get_temp_filepath(img2)
        
        # Determine parameters
        if img1.type == ImageType.DYNAMIC and img2.type == ImageType.DYNAMIC:
            # 'ffmpeg -y -i img1.gif  -ignore_loop 0 -i img2.gif -filter_complex "[0][1]overlay=format=auto:shortest=1,split[s0][s1];[s0]palettegen=reserve_transparent=1[p];[s1][p]paletteuse" ../out.gif'
            ignore_loop1 = '-ignore_loop 0'
            ignore_loop2 = ''
            shortest = '1'
        elif img1.type == ImageType.STATIC and img2.type == ImageType.DYNAMIC:
            # 'ffmpeg -y -i img1.png -i img2.gif -ignore_loop 0 -filter_complex "[0][1]overlay=format=auto:shortest=0,split[s0][s1];[s0]palettegen=reserve_transparent=1[p];[s1][p]paletteuse" ../out.gif'
            ignore_loop1 = ''
            ignore_loop2 = '-ignore_loop 0'
            shortest = '0'
        elif img1.type == ImageType.DYNAMIC and img2.type == ImageType.STATIC:
            # 'ffmpeg -y -i img1.png -i img2.gif -ignore_loop 0 -filter_complex "[0][1]overlay=format=auto:shortest=0,split[s0][s1];[s0]palettegen=reserve_transparent=1[p];[s1][p]paletteuse" ../out.gif'
            ignore_loop1 = ''
            ignore_loop2 = ''
            shortest = '0'

        ext = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['ext']
        cmd = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['cmd']
        with tempfile.NamedTemporaryFile(dir=self.temp_dir.name, suffix=ext, delete=False) as f:
            formatted_cmd = cmd.format(src1=img1.fp, src2=img2.fp, out=f.name, ig1=ignore_loop1, ig2=ignore_loop2, shortest=shortest).split()
            print(' '.join(formatted_cmd))
            subprocess.run(cmd.format(src1=img1.fp, src2=img2.fp, out=f.name, ig1=ignore_loop1, ig2=ignore_loop2, shortest=shortest).split())
        
        return ImageDescriptor(type=ImageType.DYNAMIC, fp=f.name)

    # Save the image to a file in temp_dir
    def _get_temp_filepath(self, img: ImageDescriptor) -> str:
        assert img.img is not None
        file = None
        try:
            file = tempfile.NamedTemporaryFile(dir=self.temp_dir.name, suffix=self.STATIC_EXT, delete=False)
            img.fp = file.name
            img.img.save(img.fp)
        finally:
            if file:
                file.close()

        return img.fp
        
