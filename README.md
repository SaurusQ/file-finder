# File finder

A simple python program for searching files.
Automatically extracts compressed files.
Has a interactive mode.
Tested on git bash on windows.

## Options

        positional arguments:
        directory                       Which folder is searched

        options:
        -h, --help                      show this help message and exit
        -s SEARCH [SEARCH ...], --search SEARCH [SEARCH ...]
                                        Search
        -v, --verbose                   Verbose output
        -e, --extract                   Extract zip, tar packages
        -b BEFORE, --before BEFORE      Show additional lines a match
        -a AFTER, --after AFTER         Show additional lines a match
        -l, --line                      Print line numbers
        -p, --print                     View the file contents
        -i, --interactive               Interactive search
        -g, --no-highligth              Less colorful higlighting
        --skipped                       Show skipped files
