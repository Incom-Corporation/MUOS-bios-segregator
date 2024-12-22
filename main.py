import json
import shutil
import urllib.request
from pathlib import Path
import hashlib
import argparse

URI = "http://uptothemoon.atwebpages.com/json/bios_files.json"

def create_output_dir(output_dir: Path):
    output_dir.mkdir(exist_ok=True, parents=True)

def load_bios_files():
    print("[i] Loading bios files JSON")
    return json.loads(urllib.request.urlopen(URI).read())

def parse_bios_files(output_dir: Path, bios_json: dict):
    print("[i] Parsing bios files")
    files = {b['file']: b['MD5'] for v in bios_json.values() if isinstance(v, dict) for b in v['biosFiles']}
    for file in files:
        (output_dir / file).parent.mkdir(exist_ok=True, parents=True)
    return files

def verify_existing_files(output_dir: Path, files):
    md5_mismatch = []
    for filename, md5 in list(files.items()):
        file_path = output_dir / filename
        if file_path.is_file():
            calc_md5 = hashlib.md5(file_path.read_bytes()).hexdigest()
            if calc_md5 == md5:
                files.pop(filename)
            else:
                md5_mismatch.append({"filename": filename, "md5": md5, "calc_md5": calc_md5})
                files.pop(filename)
    if md5_mismatch:
        print("[i] MD5 Mismatch:")
        for m in md5_mismatch:
            print(f"     - {m['filename']}: REQUIRED: {m['md5']}, FOUND: {m['calc_md5']}")
    return files

def copy_matching_files(source_bios_dir: Path, output_dir: Path, files):
    print("[i] Copying matching files")
    for f in source_bios_dir.rglob('*'):
        if f.is_file():
            md5 = hashlib.md5(f.read_bytes()).hexdigest()
            for fi, file_md5 in list(files.items()):
                if file_md5 == md5:
                    if not (output_dir / fi).is_file():
                        print(f"[i] Found: {fi}")
                        shutil.copyfile(f, output_dir / fi)
                    files.pop(fi)
    return files

def print_not_found_files(files):
    if len(files) > 0:
        print("[i] Not found:")
        for k, v in files.items():
            print(f"     - {k}: {v}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MUOS BIOS Downloader')
    parser.add_argument('--source-bios-dir', type=str, help='Source BIOS directory', default='source_bios')
    parser.add_argument('--zip', action='store_true', help='Zip output to installable archive')
    parser.add_argument('--mmc', action='store_true', help='Copy to MMC card')
    args = parser.parse_args()
    storage_dest = "mmc" if args.mmc else "sdcard"
    output_dir = Path(f'output/mnt/{storage_dest}/MUOS/bios')
    create_output_dir(output_dir)
    bios_files_json = load_bios_files()
    files = parse_bios_files(output_dir, bios_files_json)
    files = verify_existing_files(output_dir, files)
    files = copy_matching_files(Path(args.source_bios_dir), output_dir, files)
    print_not_found_files(files)
    if args.zip:
        filename = f'bios-{storage_dest}'
        print(f"[i] Zipping output directory into: {filename}.zip")
        shutil.make_archive(f'bios-{storage_dest}', 'zip', 'output')
