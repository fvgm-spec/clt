# img-converter

A command line tool to convert PNG images to `jpg`, `jpeg`, or `webp` formats.

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
python img_converter.py <file(s)> -f <format> [options]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `files` | yes | One or more PNG files to convert |
| `-f`, `--format` | yes | Output format: `jpg`, `jpeg`, or `webp` |
| `-o`, `--output-dir` | no | Output directory (default: `~/Pictures/Converted`) |
| `-s`, `--size` | no | Output size as `WxH` (default: `1200x630`) |

### Defaults

- Output directory: `~/Pictures/Converted/` (created automatically if it doesn't exist)
- Output size: `1200x630` px
- Maximum file size: `2 MB` (conversion is rejected and file deleted if exceeded)

## Examples

```bash
# convert a single file to jpg
python img_converter.py screenshot.png -f jpg

# convert multiple files to webp
python img_converter.py *.png -f webp

# custom output directory
python img_converter.py screenshot.png -f jpg -o ~/Desktop/output

# custom size
python img_converter.py screenshot.png -f webp -s 800x600
```

## Output

```
[ok] screenshot.png → /home/user/Pictures/Converted/screenshot.jpg
[error] Converted file exceeds 2 MB limit: large_image.jpg
[skip] missing.png — file not found
```
