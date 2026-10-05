import Vision
import AppKit

// Usage: ocr page1.png page2.png ...
// Vision OCR (Chinese + English), then emit each page's text in reading order:
// all left-column lines first, then all right-column lines.
// (Handbook pages are fixed two-column; column split by item center x = 0.5.)

let args = Array(CommandLine.arguments.dropFirst())
let langs = (ProcessInfo.processInfo.environment["OCR_LANGS"] ?? "zh-Hans,en-US")
    .split(separator: ",").map { String($0) }

struct Item {
    let text: String
    let x0: CGFloat, x1: CGFloat, y0: CGFloat, y1: CGFloat // vision bbox: y up
}

func ocrPage(_ path: String) -> [String] {
    guard let image = NSImage(contentsOfFile: path),
          let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let cgImage = bitmap.cgImage else {
        return ["[LOAD FAILED]"]
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = langs
    request.usesLanguageCorrection = true
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
    } catch {
        return ["[OCR FAILED: \(error.localizedDescription)]"]
    }
    guard let observations = request.results else { return [] }
    let items: [Item] = observations.compactMap { obs -> Item? in
        guard let candidate = obs.topCandidates(1).first else { return nil }
        let b = obs.boundingBox
        return Item(text: candidate.string, x0: b.minX, x1: b.maxX, y0: b.minY, y1: b.maxY)
    }
    // Group into lines by vertical overlap, keep items in x order inside each line
    let sorted = items.sorted { ($0.y0 + $0.y1) / 2 > ($1.y0 + $1.y1) / 2 }
    var lines: [[Item]] = []
    for item in sorted {
        var placed = false
        for i in 0..<lines.count {
            let line = lines[i]
            let lineTop = line.map(\.y1).max() ?? 0
            let lineBot = line.map(\.y0).min() ?? 1
            let overlap = min(item.y1, lineTop) - max(item.y0, lineBot)
            let ref = min(item.y1 - item.y0, lineTop - lineBot)
            if ref > 0, overlap / ref > 0.6 {
                lines[i].append(item)
                placed = true
                break
            }
        }
        if !placed { lines.append([item]) }
    }
    // Split each line into left (center < 0.5) and right parts; emit left column then right
    var left: [String] = []
    var right: [String] = []
    for line in lines {
        let ordered = line.sorted { $0.x0 < $1.x0 }
        let l = ordered.filter { ($0.x0 + $0.x1) / 2 < 0.5 }
        let r = ordered.filter { ($0.x0 + $0.x1) / 2 >= 0.5 }
        if !l.isEmpty { left.append(l.map(\.text).joined(separator: "  ")) }
        if !r.isEmpty { right.append(r.map(\.text).joined(separator: "  ")) }
    }
    return left + [""] + right
}

for path in args {
    let name = (path as NSString).lastPathComponent
    print("=== \(name) ===")
    for line in ocrPage(path) {
        print(line)
    }
}
