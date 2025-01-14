#!/usr/bin/env python3

import time
import multiprocessing as mp

from argparse import ArgumentParser
from datetime import datetime
from shutil import copyfile
from pathlib import Path

from exif import Image

def get_exif_date(path: str):
    with open(path, 'rb') as img_file:
        try:
            image = Image(img_file)
        except Exception:
            print(f"Could not examine file {path}.")
            return None

        if not image.has_exif:
            print(f"No exif data in file {path}.")
            return None

        date_str = None

        attributes = [
            "datetime_digitized",
            "datetime",
            "datetime_original"
        ]

        for attr in attributes:
            if hasattr(image, attr):
                date_str = image[attr]

        if date_str is None:
            print(f"No datetime in exif data in file {path}.")
            return None

        try:
            date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception:
            print(f"Could not parse date string {date_str} in file {path}.")
            return None

        return date

def get_date(path: str):
    #Could potentially also use date from filename 
    #as a fallback if it's present.
    return get_exif_date(path)

def create_sorted_list(dir_str: str):
    dir_path = Path(dir_str)

    if not dir_path.is_dir():
        print(f"Path {dir_str} is not a directory.")
        return None

    with_dates = []
    without_dates = []

    skip_extensions = {'.db'}

    for path in dir_path.iterdir():
        if not path.is_file():
            continue

        if path.suffix in skip_extensions:
            continue

        date = get_date(path)

        if date is None:
            without_dates.append((path, date))
        else:
            with_dates.append((path, date))

    with_dates.sort(key = lambda x: x[1])

    return with_dates + without_dates

def copy_dir(root_path: Path, target_path: Path, output_path: Path):
    trimmed = target_path.relative_to(root_path)
    target_dir = output_path / trimmed

    target_dir.mkdir(parents=True, exist_ok=True)

    photo_list = create_sorted_list(target_path)

    fill_num = len(str(len(photo_list)))

    for idx, (path, date) in enumerate(photo_list):
        src = path

        ext = path.suffix

        filename = str(1 + idx).zfill(fill_num)

        if date is None:
            filename += 'N'

        dst = target_dir / (filename + ext)

        copyfile(src, dst)

def leaf_dir_gen(root_path):
    child_dirs = [path for path in root_path.iterdir() if path.is_dir()]

    if not child_dirs:
        yield root_path
        return

    for path in child_dirs:
        yield from leaf_dir_gen(path)

def process(queue):
    while True:
        data = queue.get()
        if data is None:
            break
        copy_dir(*data)

def parse_args():
    parser = ArgumentParser(
        prog='relabel.py',
        description='Small utility for sorting photos by their exif datetime.',
    )

    parser.add_argument(
        'target_dir', type=str, 
        help='directory to copy files from.'
    )
    parser.add_argument(
        'output_dir', nargs='?', default='./Sorted', 
        help='directory to copy files to.'
    )

    args = parser.parse_args()

    return (
        Path(args.target_dir),
        Path(args.output_dir)
    )

def main():
    root_path, output_root = parse_args()

    if not root_path.is_dir():
        print(f"Path: {root_path} is not a valid directory.")
        return

    start = time.time()

    num_cores = mp.cpu_count()

    queue = mp.Queue(maxsize=num_cores)
    pool = mp.Pool(num_cores, initializer=process, initargs=(queue,))

    for dir_path in leaf_dir_gen(root_path):
        queue.put((root_path, dir_path, output_root))

    for _ in range(num_cores):
        queue.put(None)

    pool.close()
    pool.join()

    end = time.time()
    print(f"Execution took: {end - start} [s].")

if __name__ == "__main__":
    main()
