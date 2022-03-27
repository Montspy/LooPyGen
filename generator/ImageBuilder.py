
from os import path
from functools import singledispatchmethod
from PIL import Image
from typing import List, Tuple
import asyncio
import tempfile
import subprocess

# Type of image (png, jpg = STATIC - gif, mp4 = ANIMATED)
class ImageType():
    STATIC = 0
    ANIMATED = 1

# TODO: split in 2: Static/Animated
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
    FFMPEG_LOGLEVEL = '-hide_banner -loglevel warning'
    FFMPEG_PARAMS = {
        '.gif': {
            # Command and extension for compositing
            'ext': '.webm',
            'cmd': 'ffmpeg {ll} -y {codec1} {image} -i {src1} {codec2} {ig} -i {src2} -f lavfi -i anullsrc -filter_complex "{ov_order}overlay=shortest=1[ov]" -map [ov] -an -c:v libvpx-vp9 -lag-in-frames 0 -lossless 1 -row-mt 1 -pix_fmt yuva420p -shortest {out}',
            # Command and extension for final export, if any
            'final_ext': '.gif',
            'final_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -vf "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" {out}',
            # Command and extension for thumbnail export, if any (TODO: unused)
            'thumb_ext': '.gif',
            'thumb_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -vf "fps=15,scale=w={w}:h={h}:flags=lanczos:force_original_aspect_ratio=decrease,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" {out}',
        },
        '.webm': {
            # Command and extension for compositing
            'ext': '.webm',
            'cmd': 'ffmpeg {ll} -y {codec1} {image} -i {src1} {codec2} {ig} -i {src2} -f lavfi -i anullsrc -f lavfi -i anullsrc -filter_complex "amerge=inputs=2,pan=stereo|c0<c0+c2|c1<c1+c3[a]" -filter_complex "{ov_order}overlay[ov]" -map [ov] -map [a] -c:v libvpx-vp9 -lag-in-frames 0 -lossless 1 -row-mt 1 -pix_fmt yuva420p -shortest {out}',
            # Command and extension for final export, if any
            'final_ext': '.webm',
            'final_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -lag-in-frames 0 -b:v 0 -crf 20 -row-mt 1 -pix_fmt yuva420p {out}',
            # Command and extension for thumbnail export, if any (TODO: unused)
            'thumb_ext': '.gif',
            'thumb_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -vf "fps=15,scale=w={w}:h={h}:flags=lanczos:force_original_aspect_ratio=decrease,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" {out}',
        },
        '.mp4': {
            # Command and extension for compositing
            'ext': '.webm',
            'cmd': 'ffmpeg {ll} -y {codec1} {image} -i {src1} {codec2} {ig} -i {src2} -f lavfi -i anullsrc -f lavfi -i anullsrc -filter_complex "amerge=inputs=2,pan=stereo|c0<c0+c2|c1<c1+c3[a]" -filter_complex "{ov_order}overlay[ov]" -map [ov] -map [a] -c:v libvpx-vp9 -lag-in-frames 0 -lossless 1 -row-mt 1 -pix_fmt yuva420p -shortest {out}',
            # Command and extension for final export, if any
            'final_ext': '.mp4',
            'final_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -pix_fmt yuv420p {out}',
            # Command and extension for thumbnail export, if any (TODO: unused)
            'thumb_ext': '.gif',
            'thumb_cmd': 'ffmpeg {ll} -y -c:v libvpx-vp9 -i {src} -vf "fps=15,scale=w={w}:h={h}:flags=lanczos:force_original_aspect_ratio=decrease,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -movflags +faststart {out}',
        },
    }
    FFMPEG_EXT = list(FFMPEG_PARAMS.keys())

    STATIC_EXT = '.png'                 # Output format for static image NFT
    FFMPEG_MODE = '.webm'               # Output format for animated NFT
    final: ImageDescriptor              # Final result, before export
    img: ImageDescriptor                # Final exported result
    descriptors: list[ImageDescriptor]  # Queue of images required to build the final image
    temp_dir: tempfile.TemporaryDirectory

    def __init__(self, animated_format=None):
        self.FFMPEG_MODE = animated_format or self.FFMPEG_MODE
        self.img = None
        self.descriptors = []
        assert self.FFMPEG_MODE in self.FFMPEG_EXT, f"{animated_format} is not a supported format for animated NFT. Choose between {', '.join(self.FFMPEG_EXT)}."

   # Context management for temp files
    def __enter__(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir='./')
        return self

    def __exit__(self, *exc_info):
        self.temp_dir.__exit__(*exc_info)

    @singledispatchmethod
    def overlay_image(self, src, **kwds):
        raise NotImplementedError(f"Cannot overlay type: {type(src)}")

    @overlay_image.register
    def _(self, fp: str, **kwds):   # From file path
        if path.splitext(fp)[1] in self.FFMPEG_EXT:
            desc = ImageDescriptor(type=ImageType.ANIMATED, fp=fp)
        else:
            desc = ImageDescriptor(type=ImageType.STATIC, img=self._get_image(fp), fp=fp)
        self.descriptors.append(desc)

    @overlay_image.register
    def _(self, src: Image.Image, **kwds):   # From PIL.Image
        desc = ImageDescriptor(type=ImageType.STATIC, img=src)
        self.descriptors.append(desc)

    @overlay_image.register
    def _(self, rgba: tuple, size: Tuple[int], **kwds):   # From RGBA
        assert len(rgba) == 4
        src = Image.new(mode="RGBA", size=size, color=rgba)
        desc = ImageDescriptor(type=ImageType.STATIC, img=src)
        self.descriptors.append(desc)

    # Build and return the image
    async def build(self) -> ImageDescriptor:
        assert len(self.descriptors) > 0

        # Make canvas
        if self.descriptors[0].type == ImageType.STATIC:
            self._make_canvas(self.descriptors[0].img)
        elif self.descriptors[0].type == ImageType.ANIMATED:
            self._make_canvas(self.descriptors[0].fp)

        for desc in self.descriptors:
            self.img = await self.composite(self.img, desc)

        self.final = ImageDescriptor(type = self.img.type, img=self.img.img, fp=self.img.fp)
        self.img = await self.final_export(self.final)

        return self.img

    # Generate and return the thumbnail
    async def thumbnail(self, size=None) -> ImageDescriptor:
        if size is None or len(size) == 0:  # No size provided, use x = 640
            thumb_size = [640]
        else:
            thumb_size = size
        
        if len(thumb_size) == 1:    # Only x provided, calculate y
            full_size = self._get_size(self.img)
            y = int(thumb_size[0] / full_size[0] * full_size[1])
            thumb_size = [thumb_size[0], y]
        elif len(thumb_size) == 2:  # x,y provided, find thumb_size that fits within size, with aspect ratio of full_size
            full_size = self._get_size(self.img)
            scale = min(thumb_size[0] / full_size[0], thumb_size[1] / full_size[1])
            x, y = int(full_size[0] * scale), int(full_size[1] * scale)
            thumb_size = [x, y]
        
        return await self._thumb(self.final, size=thumb_size)

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
        elif desc.type == ImageType.ANIMATED:
            # Get resolution from ffprobe
            cmd = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 {desc.fp}"
            return tuple( (int(x) for x in subprocess.run(cmd.split(), capture_output=True, text=True).stdout.split(sep=',')) )

    # Compositers
    async def composite(self, img1: ImageDescriptor, img2: ImageDescriptor) -> ImageDescriptor:
        if img1.type == ImageType.STATIC and img2.type == ImageType.STATIC:
            return ImageDescriptor(type=ImageType.STATIC, img=Image.alpha_composite(img1.img, img2.img))
        else:
            # Use ffmpeg
            return await self._composite_animated(img1, img2)

    # Composite 2 animated images according to FFMPEG_MODE
    async def _composite_animated(self, img1: ImageDescriptor, img2: ImageDescriptor) -> ImageDescriptor:
        # Ensure inputs have a file on the system
        if img1.fp is None:
            self._get_temp_filepath(img1)
        if img2.fp is None:
            self._get_temp_filepath(img2)
        
        # Determine parameters
        ignore_loop = ''    # For GIFs
        image = ''          # For static images
        ov_order = '[0][1]' # Overlay order (src 1 on top of src 0 is default)
        src1 = img1.fp
        src2 = img2.fp
        if img1.type == ImageType.ANIMATED and img2.type == ImageType.ANIMATED:
            if path.splitext(src2)[1] == '.gif':
                ignore_loop = '-ignore_loop 0'
        elif img1.type == ImageType.STATIC and img2.type == ImageType.ANIMATED:
            image = '-f image2 -pattern_type none -loop 0'
            if path.splitext(src2)[1] == '.gif':
                ignore_loop = '-ignore_loop 1'
        elif img1.type == ImageType.ANIMATED and img2.type == ImageType.STATIC:
            src1, src2 = src2, src1
            ov_order = '[1][0]'
            image = '-f image2 -pattern_type none -loop 0'
            if path.splitext(src2)[1] == '.gif':
                ignore_loop = '-ignore_loop 1'

        # Determine codecs
        codec1 = ''
        codec2 = ''
        if path.splitext(src1)[1] == '.webm':
            codec1 = '-c:v libvpx-vp9'
        if path.splitext(src2)[1] == '.webm':
            codec2 = '-c:v libvpx-vp9'

        # Let ffmpeg rip
        ext = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['ext']
        cmd = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['cmd']
        with tempfile.NamedTemporaryFile(dir=self.temp_dir.name, suffix=ext, delete=False) as f:
            formatted_cmd = cmd.format(ll=self.FFMPEG_LOGLEVEL, image=image, codec1=codec1, src1=src1, ig=ignore_loop, codec2=codec2, src2=src2, ov_order=ov_order, out=f.name)
            await self._run_async_ffmpeg(formatted_cmd)
        
        return ImageDescriptor(type=ImageType.ANIMATED, fp=f.name)

    # Final exporter
    async def final_export(self, img: ImageDescriptor):
        if img.type == ImageType.STATIC:
            return img
        elif img.type == ImageType.ANIMATED:
            return await self._final_export_animated(img)

    async def _final_export_animated(self, img: ImageDescriptor):
        assert img.type == ImageType.ANIMATED
        final_ext = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['final_ext']
        final_cmd = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['final_cmd']
        if not final_cmd:
            return img
        else:
            with tempfile.NamedTemporaryFile(dir=self.temp_dir.name, suffix=final_ext, delete=False) as f:
                formatted_cmd = final_cmd.format(ll=self.FFMPEG_LOGLEVEL, src=img.fp, out=f.name)
                await self._run_async_ffmpeg(formatted_cmd)
            return ImageDescriptor(type=ImageType.ANIMATED, fp=f.name)

    # Thumbnail exporters
    async def _thumb(self, img: ImageDescriptor, size: list[int]):
        if img.type == ImageType.STATIC:
            return self._thumb_static(img=img, size=size)
        elif img.type == ImageType.ANIMATED:
            return await self._thumb_animated(img=img, size=size)

    def _thumb_static(self, img: ImageDescriptor, size: list[int]):
        assert img.type == ImageType.STATIC
        return ImageDescriptor(type=ImageType.STATIC, img=img.img.resize(size, resample=Image.LANCZOS))

    async def _thumb_animated(self, img: ImageDescriptor, size: list[int]):
        assert img.type == ImageType.ANIMATED
        thumb_ext = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['thumb_ext']
        thumb_cmd = self.FFMPEG_PARAMS[self.FFMPEG_MODE]['thumb_cmd']
        if not thumb_cmd:
            return img
        else:
            with tempfile.NamedTemporaryFile(dir=self.temp_dir.name, suffix=thumb_ext, delete=False) as f:
                formatted_cmd = thumb_cmd.format(ll=self.FFMPEG_LOGLEVEL, src=img.fp, out=f.name, w=size[0], h=size[1])
                await self._run_async_ffmpeg(formatted_cmd)
            return ImageDescriptor(type=ImageType.ANIMATED, fp=f.name)

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

    # Async command helper
    async def _run_async_ffmpeg(self, cmd: str):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode > 0:
            raise RuntimeError(f'Could not run ffmpeg command "{cmd}":\n\t{stderr.decode()}')
        return
        
