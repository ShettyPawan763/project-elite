# Project Elite: Local Privacy Scanner

Project Elite is a portfolio of projects made and updated weekly or yearly. Its first project is a small command-line tool that scans files on your machine for likely sensitive data. This version detects possible email addresses in small UTF-8 text files.

## Install

```sh
python -m pip install -e .
```

## Use

```sh
privacy-scan ./folder-to-check
```

The report contains a relative file path, line number, and finding type. It never prints the matched value or a line of file contents. The scanner skips symlinks, binary files, unreadable or non-UTF-8 files, and files larger than 1 MB.

The scan runs locally and does not make network requests. Email matching is heuristic: it can miss addresses and may flag text that is not personal data. A clean scan is not proof that a folder contains no sensitive information.

## Development

```sh
python -m unittest discover -s tests
```
