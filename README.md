# EMIS Lunch Expenses Scanner 🥪💸🔍

Simple commandline interface to scan one or multiple expenses receipts images for the price and date with Tesseract OCR and submit the results directly to the EMIS API for approval.

## Prerequisites
- python3+
- virtualenv

## Setup
Before you can install the package you need to following packages installed:

`sudo apt install tesseract-ocr libtesseract-dev`

## Development environment
`make dev-init`

## Install
Until it really is packaged, best way to install is as following:

`pip install -e .`

## Execute
`emis-expenses <path>` or `eles <path>`

## Optional arguments

| Argument | Description |
| -------- | :---------- |
| `-h`, `--help` | Show this help message and exit
| `-u USERNAME`, `--username USERNAME` | Your EMIS username |
| `-p PASSWORD`, `--password PASSWORD` | Your EMIS password, when not passed you will be prompted for the password |
| `-r`, `--recursive` | Recursive folder searching, default: `False` |
| `-s`, `--skip` | Auto submit and skip if any either date or price are missing, default: `False` |
| `-i`, `--show-image` | Show the processed result image, default: `False` |
| `-t`, `--show-text` | Show the processed text from the image, default: `False` |
| `-l LANG`, `--lang LANG` | The Tesseract language to use, default: `nld` |

### Example
`eles -u john -ti /your/path/`

This will process all images in `/your/path/` and authenticate to EMIS as `john` and prompt for the password. Argument `-t` shows the
found OCR text from the image. Argument `-i` will open a window and display
the processed image.
(bug alert: don't close the window, press any key when focused to close)

## References
* [Dutch Tesseract training data](https://github.com/tesseract-ocr/tesseract/wiki/Data-Files)
* [Improve quality Tesseract](https://github.com/tesseract-ocr/tesseract/wiki/ImproveQuality)
