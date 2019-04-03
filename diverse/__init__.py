"""
django file object methods, which reads data from FS (be carefull,
calling one of them usually should be followed by closing file descriptor)

file objects:
    - size (_get_size)
    - chunks (reading by chunks)
    - multiple_chunks (size)
    - __iter__ (chunks)
    - __exit__ (close)
    - open
    - close
image file objects:
    - width
    - height
    - _get_image_dimensions
"""

VERSION = (2, 0, 0)
