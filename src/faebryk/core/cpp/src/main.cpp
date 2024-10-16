#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

enum NodeType {
    N_GENERIC,
    N_MODULE,
    N_MODULEINTERFACE,
    N_OTHER,
};

struct GraphInterface;

struct Node {
    std::string name;
    std::string type_name;
    NodeType type;
    double py_ptr;
    GraphInterface &self_gif;
};

enum GraphInterfaceType {
    G_GENERIC,
    G_HIERARCHICAL,
    G_SELF,
    G_HIERARCHICAL_NODE,
    G_MODULE_CONNECTION,
    G_OTHER,
};

struct GraphInterface {
    Node *node = nullptr;
    GraphInterfaceType type;
    double py_ptr;

    GraphInterface(GraphInterfaceType type, double py_ptr)
      : type(type)
      , py_ptr(py_ptr) {}

    void set_node(Node *node) { this->node = node; }
    Node *get_node() const { return node; }
};

enum LinkType {
    L_GENERIC,
    L_SIBLING,
    L_PARENT,
    L_NAMED_PARENT,
    L_DIRECT,
    L_DIRECT_CONDITIONAL,
    L_DIRECT_DERIVED,
    L_OTHER,
};

struct Link {
    LinkType type;
    double py_ptr;
};

struct Path {
    std::vector<GraphInterface *> gifs;

    Path(std::vector<GraphInterface *> gifs)
      : gifs(gifs) {}
};

class Graph {

  private:
    std::vector<GraphInterface> v;
    std::vector<std::tuple<GraphInterface, GraphInterface, Link>> e;
    std::unordered_map<GraphInterface *,
                       std::unordered_map<GraphInterface *, Link *>>
        e_cache = {};

  public:
    std::unordered_map<GraphInterface *, Link *> &edges(GraphInterface *v) {
        return e_cache[v];
    }

    void add_edges(
        std::vector<std::tuple<GraphInterface, GraphInterface, Link>> &e) {
        for (auto &edge : e) {
            add_edge(std::get<0>(edge), std::get<1>(edge), std::get<2>(edge));
        }
    }

    void add_edge(GraphInterface &from, GraphInterface &to, Link &link) {
        e.push_back(std::make_tuple(from, to, link));
        e_cache[&from][&to] = &link;
        e_cache[&to][&from] = &link;
        v.push_back(from);
        v.push_back(to);
    }

    std::vector<Path> find_paths(Node &src, std::vector<Node> &dst) {
        std::cout << "find_paths" << std::endl;
        std::cout << "edge count: " << e.size() << std::endl;
        std::cout << "v count: " << v.size() << std::endl;

        // throw error if src or dst type is not MODULEINTERFACE
        if (src.type != NodeType::N_MODULEINTERFACE) {
            throw std::runtime_error("src type is not MODULEINTERFACE");
        }
        for (auto &d : dst) {
            if (d.type != NodeType::N_MODULEINTERFACE) {
                throw std::runtime_error("dst type is not MODULEINTERFACE");
            }
        }

        // TODO
        return {Path({&src.self_gif, &dst[0].self_gif})};
    }
};

int add(int i, int j) { return i + j; }

PYBIND11_MODULE(faebryk_core_cpp, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("add", &add, "A function which adds two numbers");

    py::class_<Node>(m, "Node")
        .def(py::init<std::string, std::string, NodeType, double,
                      GraphInterface &>())
        .def_readonly("py_ptr", &Node::py_ptr);

    py::class_<GraphInterface>(m, "GraphInterface")
        .def(py::init<GraphInterfaceType, double>())
        .def_property("node", &GraphInterface::get_node,
                      &GraphInterface::set_node)
        .def_readonly("py_ptr", &GraphInterface::py_ptr);

    py::class_<Link>(m, "Link")
        .def(py::init<LinkType, double>())
        .def_readonly("py_ptr", &Link::py_ptr);

    py::class_<Graph>(m, "Graph")
        .def(py::init<>())
        .def("edges", &Graph::edges)
        .def("add_edge", &Graph::add_edge)
        .def("add_edges", &Graph::add_edges)
        .def("find_paths", &Graph::find_paths, "Find paths between modules");

    py::class_<Path>(m, "Path").def_readonly("gifs", &Path::gifs);

    // Type enums
    // ---------------------------------------------------------------
    py::enum_<GraphInterfaceType>(m, "GraphInterfaceType")
        .value("GENERIC", GraphInterfaceType::G_GENERIC)
        .value("SELF", GraphInterfaceType::G_SELF)
        .value("HIERARCHICAL", GraphInterfaceType::G_HIERARCHICAL)
        .value("HIERARCHICAL_NODE", GraphInterfaceType::G_HIERARCHICAL_NODE)
        .value("MODULE_CONNECTION", GraphInterfaceType::G_MODULE_CONNECTION)
        .value("OTHER", GraphInterfaceType::G_OTHER);

    py::enum_<LinkType>(m, "LinkType")
        .value("GENERIC", LinkType::L_GENERIC)
        .value("SIBLING", LinkType::L_SIBLING)
        .value("PARENT", LinkType::L_PARENT)
        .value("NAMED_PARENT", LinkType::L_NAMED_PARENT)
        .value("DIRECT", LinkType::L_DIRECT)
        .value("DIRECT_CONDITIONAL", LinkType::L_DIRECT_CONDITIONAL)
        .value("DIRECT_DERIVED", LinkType::L_DIRECT_DERIVED)
        .value("OTHER", LinkType::L_OTHER);

    py::enum_<NodeType>(m, "NodeType")
        .value("GENERIC", NodeType::N_GENERIC)
        .value("MODULE", NodeType::N_MODULE)
        .value("MODULEINTERFACE", NodeType::N_MODULEINTERFACE)
        .value("OTHER", NodeType::N_OTHER);
}
