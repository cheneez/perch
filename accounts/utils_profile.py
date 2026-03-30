"""Profile image processing (Pillow)."""

import uuid
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image


def process_profile_image_upload(uploaded_file, max_side=400):
    """
    Resize image to fit within max_side x max_side, JPEG output.
    Returns InMemoryUploadedFile or None if no file.
    """
    if not uploaded_file:
        return None
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=88)
    buf.seek(0)
    size = buf.getbuffer().nbytes
    name = f'{uuid.uuid4().hex}.jpg'
    return InMemoryUploadedFile(
        buf,
        None,
        name,
        'image/jpeg',
        size,
        None,
    )
