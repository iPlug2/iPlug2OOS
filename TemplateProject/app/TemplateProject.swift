import CoreMIDI
import SwiftUI

@main
class TemplateProjectApp: App {
  @ObservedObject private var hostModel = AudioUnitHostModel()
  
  required init() {}
  
  var body: some Scene {
    WindowGroup {
      ContentView(hostModel: hostModel)
    }
  }
}
