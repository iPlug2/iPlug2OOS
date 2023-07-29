import AudioToolbox
import SwiftUI

struct ContentView: View {
  @ObservedObject var hostModel: AudioUnitHostModel

  var body: some View {
    VStack() {
      if let viewController = hostModel.viewModel.viewController {
        AUViewControllerUI(viewController: viewController)
      } else {
        VStack() {
          Text(hostModel.viewModel.message)
            .padding()
        }
        .frame(minWidth: 400, minHeight: 200)
      }
    }
    .ignoresSafeArea()
  }
}

struct ContentView_Previews: PreviewProvider {
  static var previews: some View {
    ContentView(hostModel: AudioUnitHostModel())
  }
}
