// Prints the horizontal centre (0–1) to frame a vertical crop on, per image:
// the largest face; if none, the most attention-grabbing region; else "none".
// usage: facecx img1.jpg img2.jpg ...   -> "<path>\t<cx|none>\t<face|salient|none>"
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("\(path)\tnone\tnone"); continue }
    let handler = VNImageRequestHandler(cgImage: cg)
    let faceReq = VNDetectFaceRectanglesRequest()
    let salReq = VNGenerateAttentionBasedSaliencyImageRequest()
    try? handler.perform([faceReq, salReq])
    let faces = (faceReq.results ?? []).sorted { $0.boundingBox.width * $0.boundingBox.height > $1.boundingBox.width * $1.boundingBox.height }
    if let f = faces.first {
        print(String(format: "%@\t%.3f\tface", path, f.boundingBox.midX))
    } else if let obj = (salReq.results?.first as? VNSaliencyImageObservation)?.salientObjects?.max(by: { $0.confidence < $1.confidence }) {
        print(String(format: "%@\t%.3f\tsalient", path, obj.boundingBox.midX))
    } else {
        print("\(path)\tnone\tnone")
    }
}
