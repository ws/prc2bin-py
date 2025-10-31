#!/usr/bin/env python3
"""
prc2bin - Extracts resources from PalmOS PRC files

Based on the original C implementation by E.Sundaw <sundaw@yahoo.com>, 1999
Rewritten in Python for modern systems.
"""

import argparse
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


# Map resource type codes to human-readable directory names
RESOURCE_TYPE_NAMES = {
    'code': 'code',
    'data': 'data',
    'pref': 'preferences',
    'NFNT': 'fonts',
    'tFRM': 'forms',
    'tSTR': 'strings',
    'tSTL': 'string-lists',
    'Talt': 'alerts',
    'Tbmp': 'bitmaps',
    'tAIB': 'app-icons',
    'tAIN': 'app-info',
    'clut': 'color-tables',
    'xloc': 'locales',
    'gdef': 'graphics-defs',
    'tver': 'version',
    'Tbtn': 'buttons',
    'tMNU': 'menus',
    'tICN': 'icons',
    'tLST': 'lists',
    'tFBM': 'form-bitmaps',
    'tgrb': 'graffiti',
    'wrdl': 'word-lists',
    'boot': 'boot-code',
    'silk': 'silk-screen',
}


def get_resource_type_dir(type_code: str) -> str:
    """
    Get a human-readable directory name for a resource type.
    Falls back to the original type code if not in the mapping.
    """
    return RESOURCE_TYPE_NAMES.get(type_code, type_code.lower())


@dataclass(frozen=True)
class PRCHeader:
    """PalmOS PRC file header structure"""
    name: bytes  # 32 bytes, zero-terminated string
    flags: int  # unsigned short
    version: int  # unsigned short
    create_time: int  # unsigned long (pilot_time_t)
    mod_time: int  # unsigned long
    backup_time: int  # unsigned long
    mod_num: int  # unsigned long
    app_info: int  # unsigned long
    sort_info: int  # unsigned long
    type: int  # unsigned long
    id: int  # unsigned long
    unique_id_seed: int  # unsigned long
    next_record_list: int  # unsigned long
    num_records: int  # unsigned short


@dataclass(frozen=True)
class ResourceHeader:
    """PRC resource header structure"""
    name: bytes  # 4 bytes
    id: int  # unsigned short
    offset: int  # unsigned long


def read_prc_header(fp: BinaryIO) -> PRCHeader:
    """Read PRC header from file (78 bytes total)"""
    data = fp.read(78)
    if len(data) != 78:
        raise ValueError(f"Invalid PRC header: expected 78 bytes, got {len(data)}")
    
    # Unpack entire header in one operation
    # Format: 32s = 32-byte string, H = unsigned short, L = unsigned long
    # All values are big-endian (>)
    unpacked = struct.unpack('>32sHHLLLLLLLLLLH', data)
    
    return PRCHeader(*unpacked)


def read_resource_header(fp: BinaryIO) -> ResourceHeader:
    """Read a single resource header (10 bytes)"""
    name = fp.read(4)
    id_val = struct.unpack('>H', fp.read(2))[0]
    offset = struct.unpack('>L', fp.read(4))[0]
    return ResourceHeader(name, id_val, offset)


def extract_resources(input_file: Path, output_dir: Path, organize_by_type: bool = False) -> int:
    """
    Extract all resources from a PRC file to the specified output directory.
    
    Args:
        input_file: Path to the PRC file
        output_dir: Directory to extract resources to
        organize_by_type: If True, create subdirectories for each resource type
    
    Returns the number of resources extracted.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(input_file, 'rb') as fp:
        # Read header
        hdr = read_prc_header(fp)
        
        # Read all resource headers
        resources = []
        for _ in range(hdr.num_records):
            resources.append(read_resource_header(fp))
        
        # Get file size for calculating last resource length
        fp.seek(0, os.SEEK_END)
        file_size = fp.tell()
        
        # Extract each resource
        for i, res in enumerate(resources):
            # Validate offset
            if res.offset >= file_size:
                print(f"Warning: Resource {i} has invalid offset 0x{res.offset:08x}, skipping")
                continue
            
            # Calculate resource length
            if i < len(resources) - 1:
                length = resources[i + 1].offset - res.offset
            else:
                length = file_size - res.offset
            
            # Generate filename: 4-char type + 4-digit hex ID + .bin
            # Use printable characters from the name, or replace non-printable with '?'
            name_str = ''.join(chr(b) if 32 <= b <= 126 else '?' for b in res.name)
            
            filename = f"{name_str}{res.id:04x}.bin"
            
            # Organize into subdirectories by type if requested
            if organize_by_type:
                type_dir_name = get_resource_type_dir(name_str)
                type_dir = output_dir / type_dir_name
                type_dir.mkdir(exist_ok=True)
                output_path = type_dir / filename
            else:
                output_path = output_dir / filename
            
            print(f"Writing {output_path} from offset 0x{res.offset:08x} "
                  f"(name={name_str} id={res.id})")
            
            # Read resource data
            fp.seek(res.offset)
            data = fp.read(length)
            
            # Write to file
            with open(output_path, 'wb') as out_fp:
                out_fp.write(data)
        
        # Write header file
        header_filename = f"{input_file.name}.hdr"
        header_path = output_dir / header_filename
        with open(header_path, 'wb') as out_fp:
            fp.seek(0)
            header_data = fp.read(78)  # PRC header is 78 bytes
            out_fp.write(header_data)
        
        print(f"{hdr.num_records} resources and header written.")
        print()
        
        return hdr.num_records


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Extracts resources from PalmOS PRC files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the PRC file to extract"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where extracted files will be written (use '.' for current directory)"
    )
    parser.add_argument(
        "-t", "--by-type",
        action="store_true",
        dest="organize_by_type",
        help="Organize extracted files into subdirectories by resource type"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: File '{args.input_file}' not found")
        sys.exit(1)
    
    try:
        extract_resources(args.input_file, args.output_dir, args.organize_by_type)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
