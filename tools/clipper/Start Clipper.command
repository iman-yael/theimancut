#!/bin/zsh
# Double-click to start The Iman Cut Clipper. macOS may ask once to let Terminal read Desktop/Documents/Downloads.
cd "${0:A:h}"
# first run: build the macOS face finder used by the optional crop mode
[[ -x facecx ]] || swiftc -O facecx.swift -o facecx
( sleep 1.5; open "http://127.0.0.1:8765" ) &
exec python3 -E server.py
