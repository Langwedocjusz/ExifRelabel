# ExifRelabel

Tiny utility for sorting photos according to time from their exif data.


## Requirements
Besides python standard library the only dependency is the [exif](https://pypi.org/project/exif/) library.

## Usage
Running
```
  ./relabel target_dir output_dir
```
will recursively copy all files from ```target_dir``` to ```output_dir```. 
Each copied file will be assigned its chronologial position in its parent directory as a filename (padded with zeroes to ensure proper display in file managers).
Files not containing valid exif data will be appended towards the end, in the same order they were in originally. Suffix ```N``` will also be added to their names.
