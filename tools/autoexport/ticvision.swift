// Frame facts for cover picking, from macOS Vision (on-device). One JSON line per image:
// {"path":..., "faces":[{"x","y","w","h","eyes","mouth","conf"}], "salient":{"x","y","w","h"}|null}
// Coordinates are 0-1 with origin at the TOP-left. eyes = eye openness (height/width, ~0.1 closed .. ~0.35 open),
// mouth = mouth openness (inner-lip height / width). Identity is never inferred.
import Foundation
import Vision
import AppKit

func openness(_ r: VNFaceLandmarkRegion2D?) -> Double? {
    guard let pts = r?.normalizedPoints, pts.count >= 4 else { return nil }
    let xs = pts.map { Double($0.x) }, ys = pts.map { Double($0.y) }
    let w = (xs.max()! - xs.min()!), h = (ys.max()! - ys.min()!)
    return w > 0 ? h / w : nil
}

for path in CommandLine.arguments.dropFirst() {
    var out: [String: Any] = ["path": path, "faces": [], "salient": NSNull()]
    if let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) {
        let lm = VNDetectFaceLandmarksRequest()
        let sal = VNGenerateAttentionBasedSaliencyImageRequest()
        let txt = VNDetectTextRectanglesRequest()
        try? VNImageRequestHandler(cgImage: cg).perform([lm, sal, txt])
        out["text"] = (txt.results ?? []).map { b -> [String: Double] in
            let r = b.boundingBox; return ["x": Double(r.minX), "y": Double(1 - r.maxY), "w": Double(r.width), "h": Double(r.height)] }
        var faces: [[String: Any]] = []
        for f in lm.results ?? [] {
            let b = f.boundingBox
            var d: [String: Any] = ["x": b.minX, "y": 1 - b.maxY, "w": b.width, "h": b.height, "conf": f.confidence]
            let le = openness(f.landmarks?.leftEye), re = openness(f.landmarks?.rightEye)
            if let l = le, let r = re { d["eyes"] = min(l, r) } else if let e = le ?? re { d["eyes"] = e }
            if let m = openness(f.landmarks?.innerLips) { d["mouth"] = m }
            faces.append(d)
        }
        out["faces"] = faces
        if let o = (sal.results?.first as? VNSaliencyImageObservation)?.salientObjects?.max(by: { $0.confidence < $1.confidence }) {
            let b = o.boundingBox
            out["salient"] = ["x": b.minX, "y": 1 - b.maxY, "w": b.width, "h": b.height]
        }
    }
    if let data = try? JSONSerialization.data(withJSONObject: out), let s = String(data: data, encoding: .utf8) { print(s) }
}
