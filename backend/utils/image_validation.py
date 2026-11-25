"""Bounded validation and normalization for private media uploads."""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename


MAX_IMAGE_BYTES = 3 * 1024 * 1024
MAX_IMAGE_DIMENSION = 6000
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_FORMATS = {
    'JPEG': ('image/jpeg', 'jpg'),
    'PNG': ('image/png', 'png'),
}


class ImageValidationError(ValueError):
    def __init__(self, message, *, status_code=400):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class NormalizedImage:
    data: bytes
    display_filename: str
    content_type: str
    extension: str
    byte_size: int
    width: int
    height: int
    sha256_hex: str


def _read_bounded(stream):
    try:
        raw = stream.read(MAX_IMAGE_BYTES + 1)
    except OSError:
        raise ImageValidationError('The image could not be read.') from None
    if len(raw) > MAX_IMAGE_BYTES:
        raise ImageValidationError(
            'Image must be 3 MiB or smaller.',
            status_code=413,
        )
    if not raw:
        raise ImageValidationError('Choose a non-empty JPEG or PNG image.')
    return raw


def _check_dimensions(width, height):
    if width < 1 or height < 1:
        raise ImageValidationError('Image dimensions are invalid.')
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ImageValidationError(
            f'Image dimensions must not exceed {MAX_IMAGE_DIMENSION} x '
            f'{MAX_IMAGE_DIMENSION} pixels.'
        )
    if width * height > MAX_IMAGE_PIXELS:
        raise ImageValidationError('Image contains too many pixels.')


def _display_filename(original_filename, extension):
    safe_name = secure_filename(original_filename or '')
    safe_stem = secure_filename(Path(safe_name).stem)[:120] or 'salon-image'
    return f'{safe_stem}.{extension}'


def normalize_uploaded_image(file_storage):
    """Validate an uploaded image and return metadata-stripped canonical bytes."""
    if file_storage is None or not getattr(file_storage, 'stream', None):
        raise ImageValidationError('An image file is required.')

    raw = _read_bounded(file_storage.stream)
    try:
        with Image.open(BytesIO(raw)) as probe:
            source_format = str(probe.format or '').upper()
            if source_format not in ALLOWED_FORMATS:
                raise ImageValidationError('Only JPEG and PNG images are supported.')
            _check_dimensions(*probe.size)
            if getattr(probe, 'is_animated', False) or getattr(probe, 'n_frames', 1) != 1:
                raise ImageValidationError('Animated images are not supported.')
            probe.verify()

        with Image.open(BytesIO(raw)) as source:
            source_format = str(source.format or '').upper()
            _check_dimensions(*source.size)
            if getattr(source, 'is_animated', False) or getattr(source, 'n_frames', 1) != 1:
                raise ImageValidationError('Animated images are not supported.')
            source.load()
            has_alpha = source.mode in {'RGBA', 'LA'} or 'transparency' in source.info
            corrected = ImageOps.exif_transpose(source)
            _check_dimensions(*corrected.size)

            output = BytesIO()
            content_type, extension = ALLOWED_FORMATS[source_format]
            if source_format == 'JPEG':
                normalized = corrected.convert('RGB')
                normalized.save(
                    output,
                    format='JPEG',
                    quality=90,
                    optimize=True,
                    progressive=False,
                    subsampling='4:2:0',
                )
            else:
                normalized = corrected.convert('RGBA' if has_alpha else 'RGB')
                normalized.save(
                    output,
                    format='PNG',
                    optimize=True,
                    compress_level=9,
                )

            normalized_bytes = output.getvalue()
            width, height = normalized.size
    except ImageValidationError:
        raise
    except (
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
    ):
        raise ImageValidationError('The image is corrupted or has an invalid format.') from None

    if not normalized_bytes or len(normalized_bytes) > MAX_IMAGE_BYTES:
        raise ImageValidationError(
            'The normalized image exceeds the 3 MiB limit.',
            status_code=413,
        )

    return NormalizedImage(
        data=normalized_bytes,
        display_filename=_display_filename(file_storage.filename, extension),
        content_type=content_type,
        extension=extension,
        byte_size=len(normalized_bytes),
        width=width,
        height=height,
        sha256_hex=sha256(normalized_bytes).hexdigest(),
    )


def build_media_object_key(extension, *, production=False):
    """Generate an opaque key without using a client filename."""
    if extension not in {'jpg', 'png'}:
        raise ImageValidationError('Unsupported normalized image extension.')
    scope = 'production' if production else 'demo'
    return f'{scope}/media/{uuid.uuid4().hex}.{extension}'
