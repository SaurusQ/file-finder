import argparse
from msilib.schema import _Validation_records
import os
import tarfile
import zipfile
import re

# Configuration
bannedFileTypes = ["bin", "exe"]
bannedFileNames = []

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Which folder is searched")
parser.add_argument("-s", "--search", nargs="+", default=[], help="Search")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
parser.add_argument("-e", "--extract", action="store_true", help="Extract zip, tar packages")
parser.add_argument("-b", "--before", type=int, default=0, help="Show additional lines before a match")
parser.add_argument("-a", "--after", type=int, default=0, help="Show additional lines after a match")
parser.add_argument("-l", "--line", action="store_true", help="Print line numbers")
parser.add_argument("--skipped", action="store_true", help="Show skipped files")

args = parser.parse_args()

searchWords = ["test"]
for w in args.search:
    searchWords.append(w)

BLACK           = (  0,   0,   0)
GREY            = ( 10,  10,  10)
RED             = (255,   0,   0)
DARK_RED        = (140,   0,   0)
VAL_RED         = (189, 113, 124)
GREEN           = (  0, 255,   0)
LIME_GREEN      = ( 50, 205,  50)
FOREST_GREEN    = ( 34, 139,  34)
BLUE            = (  0,   0, 255)
LIGHT_BLUE      = ( 50, 150, 255)
ELEC_BLUE       = (125, 249, 255)
YELLOW          = (255, 255,   0)
DARK_YELLOW     = (139, 128,   0)

matches = 0
foundInFiles = 0

def handleFileType(subdir, filepath, filename):
    
    # Handle banned files
    if filename in bannedFileNames:
        return False

    # Get filetype
    try: 
        _, filetype = filepath.rsplit(".", 1)
    except Exception as e:
        return True

    # Check that the filetype is not banned
    if filetype in bannedFileTypes:
        return False

    # Handle extraction
    if filetype in ["zip", "tar"]:
        if args.extract:
            outputPath = os.path.join(subdir, filename[::-1].replace(".","e_",1)[::-1])
            if not os.path.exists(outputPath):
                os.mkdir(outputPath)
                if filetype == "zip":
                        print("Extracting zip file")
                        zfile = zipfile.ZipFile(filepath, "r")
                        zfile.extractall(outputPath)
                        zfile.close()
                elif filetype == "tar":
                        print("Extracting tar file")
                        tfile = tarfile.open(filepath)
                        tfile.extractall(outputPath)
                        tfile.close()
                walk(outputPath)
        return False
    return True

def handleFile(filepath):
    global matches, foundInFiles
    file = open(filepath, "r")

    foundMatch = False
    lineBefore = [""] * args.before
    beforeSize = 0
    pafter = 0
    lineNumber = 0

    for line in file:
        lineNumber += 1
        # Force line break to the last line
        if line[-1] != "\n":
            line += "\n"
        for w in searchWords:
            idx = line.find(w)
            if idx != -1:
                matches += 1
                # Print the file path when some match is found
                if not foundMatch:
                    foundInFiles += 1
                    foundMatch = True
                    print(colorLine(filepath, YELLOW))
                else:
                    if beforeSize > args.before:
                        print(colorLine("------", LIGHT_BLUE))
                # Print lines before a match
                for i in reversed(range(min(beforeSize, args.before))):
                    printLineNumber(lineNumber - i - 1)
                    printLine(lineBefore[(lineNumber - i - 1) % args.before])
                beforeSize = 0
                # Print the matched line
                printLineNumber(lineNumber)
                printLine(line, idx, idx + len(w))
                pafter = args.after
                break
            # Printing after a match
            elif pafter:
                pafter -= 1
                printLineNumber(lineNumber)
                printLine(line)
                continue
            # Save lines to print before a match
            elif args.before > 0:
                beforeSize += 1
                lineBefore[lineNumber % args.before] = line
    return foundMatch


def printLine(line, sidx=None, eidx=None):
    # Basic printout
    #if sidx == None:
    #    print(line, end="")
    #else:
    #   print(lineColor(line, [(sidx, eidx, RED, False)]), end="")

    colors = []
    # Match highlight
    if sidx != None and eidx != None:
        colors.append((sidx, eidx, DARK_RED, True))
        #colors.append((sidx, eidx, BLACK, False))

    # Time stamps
    matches = re.finditer("(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)((-(\d{2}):(\d{2})|Z)?)", line)
    for m in matches:
        colors.append((m.start(), m.end(), FOREST_GREEN, False))

    # Log level
    matches = re.finditer("(DEBUG)|(INFO)|(INFORMATION)|(WARN)|(WARNING)|(ERROR)|(FAIL)|(FAILURE)", line)
    for m in matches:
        colors.append((m.start(), m.end(), VAL_RED, False))
    
    # Std constants
    matches = re.finditer("(null)|(true)|(false)", line)
    for m in matches:
        colors.append((m.start(), m.end(), ELEC_BLUE, False))

    # String constants
    matches = re.finditer("\"[^\"]*\"", line)
    for m in matches:
        colors.append((m.start(), m.end(), VAL_RED, False))

    # Numeric constants
    # GUIDS/MAC addresses
    # words ending with Exception
    # Urls
    # Namespaces

    # Printout
    print(lineColor(line, colors), end="")
    


def printLineNumber(lineNumber):
    if args.line:
        print(getColor(LIGHT_BLUE) + "{0: >5}:".format(lineNumber) + getDefaultColor(), end="")

def colorLine(line, color, bg=False):
    return getColor(color, bg) + line + getDefaultColor(bg)

def lineColor(line, colorInfo):
    result= ""
    handledIdx = 0
    ci = sorted(colorInfo)
    ends = []
    def handleEnd(startIdx):
        nonlocal result, handledIdx, ends
        while len(ends) > 0 and startIdx >= ends[-1][0]:
            e = ends.pop()
            result += line[handledIdx:e[0]]
            handledIdx = e[0]
            if len(ends) > 0 and startIdx >= ends[-1][0]:
                result += getColor(ends[-1][1], ends[-1][2])
            else:
                result += getDefaultColor()
    for sidx, eidx, color, bg in ci:
        # Handle the end of colors
        handleEnd(sidx)
        # Handle the start of color
        result += line[handledIdx:sidx] + getColor(color, bg)
        handledIdx = sidx
        # Filter overridden ends
        ends = list(filter(lambda a: a[0] > eidx, ends))
        ends.append((eidx, color, bg))
    handleEnd(float("inf"))
    result += line[handledIdx:]
    return result

def getColor(color, background=False):
    if background:
        bg = 48
    else:
        bg = 38
    return "\033[{};2;{};{};{}m".format(bg, color[0], color[1], color[2])

def getDefaultColor(background=False):
    return "\033[0m"
    if background:
        return "\033[48;2;0;0;0m"
    else:
        return "\033[38;2;255;255;255m"

skippedFiles = []
filesToParse = []

def walk(walkpath):
    # Iterate over all of the files
    for subdir, _, files in os.walk(walkpath):
        for f in files:
            path = os.path.join(subdir, f)
            if handleFileType(subdir, path, f):
                filesToParse.append(path)
            else:
                skippedFiles.append(path)

def parse():
    # Run search on all valid files
    nothingFound = []
    for filepath in filesToParse:
        if not handleFile(filepath):
            nothingFound.append(filepath)
    if args.skipped:
        print(colorLine("Skipped:", YELLOW))
        for filepath in skippedFiles:
            print(colorLine(filepath, RED))
        print(colorLine("Found nothing:", YELLOW))
        for filepath in nothingFound:
            print(colorLine(filepath, RED))

def printStats():
    print(colorLine("Found " + str(matches) + " matches inside " + str(foundInFiles) + " different files", GREEN))

#retval = lineColor("123456789012345678901234567890", [(0, 10, (255,0,0), False), (8, 20, (0, 255, 0), False), (5, 25, (0,0,255), False)])
#print(retval)

walk(args.directory)
parse()
printStats()