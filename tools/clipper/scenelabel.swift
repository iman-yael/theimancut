// Describes what is in each frame using macOS Vision's built-in scene classifier.
// usage: scenelabel img1.jpg ...  ->  "<path>\t<faces>\t<label:conf,label:conf,...>"
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("\(path)\t0\t"); continue }
    let cls = VNClassifyImageRequest()
    let faces = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: cg).perform([cls, faces])
    let top = (cls.results ?? []).filter { $0.confidence > 0.15 }.prefix(8)
        .map { String(format: "%@:%.2f", $0.identifier, $0.confidence) }.joined(separator: ",")
    print("\(path)\t\(faces.results?.count ?? 0)\t\(top)")
}
