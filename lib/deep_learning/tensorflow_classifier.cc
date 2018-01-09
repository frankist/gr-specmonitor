#include "tensorflow/core/public/session.h"
#include "tensorflow/core/platform/env.h"

// tips : https://medium.com/jim-fleming/loading-a-tensorflow-graph-with-the-c-api-4caaff88463f
// build command: bazel build :loader --verbose_failures --config=monolithic

typedef tensorflow tf;

class TfPbClassifier {
  tf::Session* session;
  tf::Status status;
public:
  std::vector<tensorflow::Tensor> outputs;
  std::vector<std::pair<string, tensorflow::Tensor> > inputs;

  void setup(const std::string& pb_file);
  void clear();
  void run();
};

TfPbClassifier::TfPbClassifier() :
  session(NULL) {
}

void TfPbClassifier::setup(const std::string& pb_file) {
  clear();
  status = tf::NewSession(tf::SessionOptions(), &session);
  if (!status.ok()) {
    std::cout << status.ToString() << "\n";
    return 1;
  }

  // Read in the protobuf graph we exported
  // (The path seems to be relative to the cwd. Keep this in mind
  // when using `bazel run` since the cwd isn't where you call
  // `bazel run` but from inside a temp folder.)
  tf::GraphDef graph_def;
  // status = ReadBinaryProto(Env::Default(), "models/graph.pb", &graph_def);
  status = tf::ReadBinaryProto(tf::Env::Default(), pb_file, &graph_def);
  if (!status.ok()) {
    std::cout << status.ToString() << "\n";
    return 1;
  }

  // Add the graph to the session
  status = session->Create(graph_def);
  if (!status.ok()) {
    std::cout << status.ToString() << "\n";
    return 1;
  }
}

void TfPbClassifier::clear() {
  if(session!=NULL) {
    // Free any resources used by the session
    session->Close();
    session=NULL;
  }
}

void TfPbClassifier::run() {
  // Our graph doesn't require any inputs, since it specifies default values,
  // but we'll change an input to demonstrate.
  Tensor a(DT_FLOAT, TensorShape());
  a.scalar<float>()() = 3.0;

  Tensor b(DT_FLOAT, TensorShape());
  b.scalar<float>()() = 2.0;

  inputs = {
    { "a", a },
    { "b", b },
  };

  // Run the session, evaluating our "c" operation from the graph
  status = session->Run(inputs, {"c"}, {}, &outputs);
  if (!status.ok()) {
    std::cout << status.ToString() << "\n";
    return 1;
  }

  // Grab the first output (we only evaluated one graph node: "c")
  // and convert the node to a scalar representation.
  auto output_c = outputs[0].scalar<float>();

  // (There are similar methods for vectors and matrices here:
  // https://github.com/tensorflow/tensorflow/blob/master/tensorflow/core/public/tensor.h)
  // Print the results
  // std::cout << outputs[0].DebugString() << "\n"; // Tensor<type: float shape: [] values: 30>
  // std::cout << output_c() << "\n"; // 30
}
