# prc2bin

A Python tool to extract resources from PalmOS PRC files.

## Description

`prc2bin` extracts all resources from a PalmOS PRC (Palm Resource Code) file and saves them as individual binary files. It also saves the PRC header to a separate `.hdr` file.

This is a modern Python reimplementation of the original C version by E.Sundaw (1999).

## Installation

This tool requires Python 3.10 or higher and has no external dependencies.

```bash
# Make the script executable
chmod +x main.py
```

## Usage

```bash
./main.py <input-file> <output-directory> [OPTIONS]
```

### Arguments

- `input-file`: Path to the PRC file to extract
- `output-directory`: Directory where extracted files will be written (use `.` for current directory)

### Options

- `-t, --by-type`: Organize extracted files into subdirectories by resource type (e.g., `code/`, `forms/`, `fonts/`, `bitmaps/`)

### Examples

Extract to current directory:
```bash
./main.py myapp.prc .
```

Extract and organize by resource type:
```bash
./main.py myapp.prc extracted/ --by-type
```

This will extract:
- Each resource as `<TYPE><ID>.bin` (e.g., `CODE0001.bin`, `tAIN1000.bin`)
- The header as `myapp.prc.hdr`
- With `--by-type`, files are organized into human-readable subdirectories:
  - `code/` - Executable code segments
  - `forms/` - UI form definitions
  - `fonts/` - Font resources
  - `strings/` - String resources
  - `bitmaps/` - Image resources
  - `app-icons/` - Application icons
  - `color-tables/` - Color palettes
  - `locales/` - Localization resources
  - And more...

## Output Format

Each resource is saved with a filename composed of:
- 4-character resource type (from the PRC resource header)
- 4-digit hexadecimal resource ID
- `.bin` extension

Example filenames:
- `CODE0001.bin` - Code resource with ID 0x0001
- `tAIN1000.bin` - tAIN resource with ID 0x1000
- `data03e8.bin` - data resource with ID 0x03e8

## PRC File Format

PalmOS PRC files contain:
1. A 78-byte header with metadata (app name, timestamps, etc.)
2. Resource headers listing each resource's type, ID, and offset
3. The actual resource data

All multi-byte values in PRC files are stored in big-endian (network) byte order.

## License

Based on the original work by E.Sundaw <sundaw@yahoo.com>, 1999.