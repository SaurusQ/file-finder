import argparse
import os
import shutil
import tarfile
from turtle import fd
import zipfile
import re
import sys
import math

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
parser.add_argument("-p", "--print", action="store_true", help="View the file contents")
parser.add_argument("-i", "--interactive", action="store_true", help="Interactive search")
parser.add_argument("-g", "--no-highligth", action="store_true", help="Remove all colors from the cli except the search term.")
parser.add_argument("--skipped", action="store_true", help="Show skipped files")

args = parser.parse_args()

searchWords = ["test"]
for w in args.search:
    searchWords.append(w)

if args.print: # Empty search words for viewing
    searchWords = []

BLACK           = (  0,   0,   0)
GREY            = ( 10,  10,  10)
RED             = (255,   0,   0)
DARK_RED        = (140,   0,   0)
LIGHT_RED       = (240, 113, 124)
FIRE_BRICK      = (178,  34,  34)
TOMATO          = (255,  99,  71)
DARK_ORANGE     = (255, 140,   0)
GREEN           = (  0, 255,   0)
LIME_GREEN      = ( 50, 205,  50)
FOREST_GREEN    = ( 63, 220, 107)
LIGHT_SEA_GREEN = ( 32, 178, 170)
AQUA_MARINE     = (127, 255, 212)
BLUE            = (  0,   0, 255)
LIGHT_BLUE      = ( 16, 177, 254)
ELEC_BLUE       = (125, 249, 255)
YELLOW          = (255, 255,   0)
DARK_YELLOW     = (139, 128,   0)
PINK            = (255, 120, 248)


matches = []
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
                        print("Extracting zip file", filepath)
                        zfile = zipfile.ZipFile(filepath, "r")
                        zfile.extractall(outputPath)
                        zfile.close()
                elif filetype == "tar":
                        print("Extracting tar file", filepath)
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

        if args.print:
            if not foundMatch:
                foundMatch = True
                matches.append(((0, 0), 0, filepath))
                foundInFiles += 1
                print(colorLine(filepath, YELLOW))
            if args.line:
                printLineNumber(lineNumber)
            printLine(line)
        else:
            lineMatch = False
            for w in searchWords:
                idx = line.find(w)
                if idx != -1:
                    # Store matches
                    matches.append(((idx, idx + len(w)), lineNumber, filepath))
                    lineMatch = True
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
            if not lineMatch:
                if pafter:
                    pafter -= 1
                    printLineNumber(lineNumber)
                    printLine(line)
                    continue
                # Save lines to print before a match
                elif args.before > 0:
                    beforeSize += 1
                    lineBefore[lineNumber % args.before] = line
    file.close()
    return foundMatch


def printLine(line, sidx=None, eidx=None):
    # Basic printout
    #if sidx == None:
    #    print(line, end="")
    #else:
    #   print(lineColor(line, [(sidx, eidx, RED, False)]), end="")

    colors = []
    ignoreRange = []

    # Match highlight
    if sidx != None and eidx != None:
        if args.no_highligth:
            colors.append((sidx, eidx, RED, False))
        else:
            colors.append((sidx, eidx, DARK_RED, True))
            colors.append((sidx, eidx, BLACK, False))

    if not args.no_highligth:
        def addColors(m, c, bg=False):
            nonlocal colors, ignoreRange
            for i in m:
                ignore = False
                # Don't override other coloring
                for r in ignoreRange:
                    if (r[0] <= i.start() < r[1]) or (r[0] < i.end() <= r[1]):
                        ignore = True
                        break
                # Shoul we use this color
                if not ignore:
                    colors.append((i.start(), i.end(), c, bg))
                    ignoreRange.append((i.start(), i.end()))

        # Time stamps
        matches = re.finditer("(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)((-(\d{2}):(\d{2})|Z)?)", line)
        addColors(matches, FOREST_GREEN)

        # Log level
        matches = re.finditer("(DEBUG)|(INFO)|(INFORMATION)|(WARN)|(WARNING)|(ERROR)|(FAIL)|(FAILURE)", line)
        addColors(matches, AQUA_MARINE)
        
        # Std constants
        matches = re.finditer("(null)|(true)|(false)|(class)|(def)", line)
        addColors(matches, ELEC_BLUE)

        # String constants
        matches = re.finditer("\"[^\"]*\"", line)
        addColors(matches, TOMATO)

        # Numeric constants
        matches = re.finditer("(?<![A-Za-z0-9.])[0-9.]+(?![A-Za-z0-9.])", line)
        addColors(matches, PINK)
        
        # Urls
        matches = re.finditer("(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", line)
        addColors(matches, BLUE)

        # Namespaces
        matches = re.finditer("([\w]+\.)+[\w]+(?=[\s]|$)", line)
        addColors(matches, LIGHT_SEA_GREEN)

        # GUIDS/MAC addresses
        # words ending with Exception

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
    # Check if the target if file
    if os.path.isfile(walkpath):
        filesToParse.append(walkpath)
        return
    
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
    print(colorLine("Found " + str(len(matches)) + " matches inside " + str(foundInFiles) + " different files", GREEN))
    getTerminalSize()

def printInteractiveHelp():
    print()
    print("[q]          quit the program")
    print("[h]          show this message")
    print("[right]      next match")
    print("[left]       previous match")
    print("[ctrl]       match in next file")
    print("[up/down]    scroll file")
    print(":", end="")
    sys.stdout.flush()

def interactiveFile(matchIdx, lineNum, filepath, lineOffset, terminal, currentMatchIdx):
    file = open(filepath, "r")
    lines = file.readlines()
    terminalRows = terminal[0]
    terminalWidth = terminal[1]
    terminalRows -= 2
    begin = int(max(1, lineNum - (terminalRows / 2) + lineOffset)) - 1
    end = min(len(lines), begin + terminalRows - 1)
    usedLines = (end - begin)
    emptyLines = terminalRows - usedLines
    print()
    print(colorLine(filepath + " m: " + str(currentMatchIdx + 1) + " / " + str(len(matches)), YELLOW)) # Current file
    for i in range(begin, end):
        line = lines[i]
        if line[-1] != "\n":
            line += "\n"
        lineWidth = math.ceil((args.line * 6 + len(line)) / terminalWidth)
        usedLines -= lineWidth
        if usedLines < 0:
            emptyLines += usedLines
            if emptyLines < 0:
                emptyLines -= usedLines
                break
            usedLines = 0
        if args.line:
            printLineNumber(i + 1)
        if i + 1 == lineNum: # Match line
            printLine(line, matchIdx[0], matchIdx[1])
        else: # Other lines
            printLine(line)
    for i in range(emptyLines):
        print()
    print(":", end="")
    sys.stdout.flush()
    file.close()
    
def getTerminalSize():
    retval = (80, 24)
    try:
        ts = os.get_terminal_size()
        retval = (ts.lines, ts.columns)
    except Exception as e:
        import subprocess
        try:
            cols = int(subprocess.check_output("tput cols"))
            rows = int(subprocess.check_output("tput lines"))
            retval = (rows, cols)
        except:
            pass
    return retval

def interactive():
    from pynput import keyboard

    lineOffset = 0
    currentMatchIdx = 0
    
    ctrlPressed = False
    def onRelease(key):
        nonlocal ctrlPressed
        if key == keyboard.Key.ctrl_l:
            ctrlPressed = False

    def onPress(key):
        nonlocal lineOffset, currentMatchIdx, ctrlPressed
        terminalSize = getTerminalSize()
        printInteractiveFile = False
        if key == keyboard.Key.up or key == keyboard.Key.down:
            if key == keyboard.Key.up:
                lineOffset -= 1
            elif key == keyboard.Key.down:
                lineOffset += 1
            matchIdx, lineNumber, filepath = matches[currentMatchIdx]
            lineOffset = max(-lineNumber + (terminalSize[0] / 2), lineOffset)
            printInteractiveFile = True
        elif key == keyboard.Key.right or key == keyboard.Key.left:
            if key == keyboard.Key.right:
                if ctrlPressed:
                    _, _, originalFilepath = matches[currentMatchIdx]
                    while True:
                        currentMatchIdx += 1
                        if currentMatchIdx >= len(matches):
                            break
                        _, _, newFilepath = matches[currentMatchIdx]
                        if originalFilepath != newFilepath:
                            break
                else:
                    currentMatchIdx += 1
            elif key == keyboard.Key.left:
                if ctrlPressed:
                    _, _, originalFilepath = matches[currentMatchIdx]
                    while True:
                        currentMatchIdx -= 1
                        if currentMatchIdx < 0:
                            break
                        _, _, newFilepath = matches[currentMatchIdx]
                        if originalFilepath != newFilepath:
                            break
                else:
                    currentMatchIdx -= 1
            # Limit the idx range
            if currentMatchIdx >= len(matches):
                currentMatchIdx = 0
            elif currentMatchIdx < 0:
                currentMatchIdx = len(matches) - 1
            
            lineOffset = 0
            printInteractiveFile = True
        elif key == keyboard.Key.ctrl_l:
            ctrlPressed = True
        elif key == keyboard.KeyCode.from_char("l"):
            args.line = not args.line
            printInteractiveFile = True
        elif key == keyboard.KeyCode.from_char("h"):
            printInteractiveHelp()
        elif key == keyboard.KeyCode.from_char("q"):
            return False

        if printInteractiveFile:
            matchIdx, lineNumber, filepath = matches[currentMatchIdx]
            interactiveFile(matchIdx, lineNumber, filepath, lineOffset, terminalSize, currentMatchIdx)
        return True

        
    with keyboard.Listener(on_press=onPress, on_release=onRelease) as listener:
        listener.join()
    listener.stop()

#retval = lineColor("123456789012345678901234567890", [(0, 10, (255,0,0), False), (11,20, (0,255,0), False)])#, (8, 20, (0, 255, 0), False), (5, 25, (0,0,255), False)])
#print(retval)

walk(args.directory)
parse()
printStats()

sys.stdout.flush()

if args.interactive:
    interactive()
