#!/bin/zsh
# Double-click to start The Iman Cut Clipper. macOS may ask once to let Terminal read Desktop/Documents/Downloads.
cd "${0:A:h}"
# first run: build the macOS helpers (face finder for crop mode, scene labels for clip names)
[[ -x facecx ]] || swiftc -O facecx.swift -o facecx
[[ -x scenelabel && scenelabel -nt scenelabel.swift ]] || swiftc -O scenelabel.swift -o scenelabel
( sleep 1.5; open "http://127.0.0.1:8765" ) &
exec python3 -E server.py
