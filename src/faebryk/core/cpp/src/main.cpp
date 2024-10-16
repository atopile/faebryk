#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "graph.hpp"
#include "pathfinder.hpp"

// TODO remove?
// check if c++20 is used
#if __cplusplus < 202002L
#error "C++20 is required"
#endif

std::vector<Path> find_paths(Graph &g, Node &src, std::vector<Node> &dst) {
    PathFinder pf(g);
    return pf.find_paths(src, dst);
}

namespace py = pybind11;

PYBIND11_MODULE(faebryk_core_cpp, m) {
    m.doc() = "faebryk core cpp graph";
    m.def("find_paths", &find_paths, "Find paths between modules");

    py::class_<Node>(m, "Node")
        .def(py::init<std::string, std::string, NodeType, uint64_t,
                      GraphInterface &>())
        .def_readonly("py_ptr", &Node::py_ptr);

    py::class_<GraphInterface>(m, "GraphInterface")
        .def(py::init<GraphInterfaceType, uint64_t, Graph &>())
        //.def_property("node", &GraphInterface::get_node,
        //              &GraphInterface::set_node)
        .def("set_node", &GraphInterface::set_node)
        .def_readonly("py_ptr", &GraphInterface::py_ptr)
        .def("make_hierarchical", &GraphInterface::make_hierarchical);

    py::class_<Link>(m, "Link")
        .def(py::init<LinkType, uint64_t>())
        .def_readonly("py_ptr", &Link::py_ptr);

    py::class_<Graph>(m, "Graph")
        .def(py::init<>())
        .def("edges", &Graph::edges)
        .def("add_edge", &Graph::add_edge)
        .def("add_edges", &Graph::add_edges);

    py::class_<Path>(m, "Path").def_readonly("gifs", &Path::gifs);

    // Type enums
    // ---------------------------------------------------------------
    py::enum_<GraphInterfaceType>(m, "GraphInterfaceType")
        .value("GENERIC", GraphInterfaceType::G_GENERIC)
        .value("SELF", GraphInterfaceType::G_SELF)
        .value("HIERARCHICAL", GraphInterfaceType::G_HIERARCHICAL)
        .value("HIERARCHICAL_NODE", GraphInterfaceType::G_HIERARCHICAL_NODE)
        .value("HIERARCHICAL_MODULE_SPECIAL",
               GraphInterfaceType::G_HIERARCHICAL_MODULE_SPECIAL)
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
