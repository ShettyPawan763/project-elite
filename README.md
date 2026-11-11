# Project Elite: Local Privacy Scanner

Project Elite is a portfolio of projects made and updated weekly or yearly. Its first project is a local privacy scanner for finding likely sensitive data in small UTF-8 text files. It checks for possible email addresses, recognizable GitHub tokens, AWS access key IDs, and credential assignments. Choose either the desktop app or command line.

## Desktop app

Download the package for your operating system from [GitHub Releases](https://github.com/ShettyPawan763/project-elite/releases). On Windows, extract the ZIP and run `Local Privacy Scanner.exe`. On macOS or Linux, extract the ZIP and run the `Local Privacy Scanner` app inside. The first release packages are built from tagged versions by GitHub Actions. These are portable app bundles, not installers; the app is not currently code-signed.

The app lets you choose a folder, optionally enter exclusion patterns (one per line), and view findings without printing matched values or file contents. It scans locally and does not upload files.

## Install

```sh
python -m pip install -e .
```

Launch the desktop interface with:

```sh
privacy-scan-gui
```

Tkinter is included with most standard Python installations. On some Linux distributions, you may need to install the system package that provides Tkinter.

## Use

```sh
privacy-scan ./folder-to-check
```

Skip paths with repeatable relative glob patterns:

```sh
privacy-scan ./folder-to-check --exclude 'build/**' --exclude '*.log'
```

The report contains a relative file path, line number, and finding type. It never prints the matched value or a line of file contents. The scanner skips excluded paths, symlinks, binary files, unreadable or non-UTF-8 files, and files larger than 1 MB.

The scan runs locally and does not make network requests. Pattern matching is heuristic: it can miss sensitive values and may flag harmless text. The scanner does not validate credentials with their providers. A clean scan is not proof that a folder contains no sensitive information.

## Development

```sh
python -m unittest discover -s tests
```


