#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "pathfinder.hpp"

// check if c++20 is used
#if __cplusplus < 202002L
#error "C++20 is required"
#endif

std::pair<std::vector<Path>, std::vector<Counter>> find_paths(Graph &g, Node &src,
                                                              std::vector<Node> &dst) {
    PerfCounter pc;

    PathFinder pf(g);
    auto res = pf.find_paths(src, dst);

    printf("TIME: %3.2lf ms C++ find paths\n", pc.ms());
    return res;
}

void configure(bool indv_measure, uint32_t max_paths) {
    INDIV_MEASURE = indv_measure;
    MAX_PATHS = max_paths;
}

namespace py = pybind11;

PYBIND11_MODULE(faebryk_core_cpp, m) {
    m.doc() = "faebryk core cpp graph";
    m.def("find_paths", &find_paths, "Find paths between modules");
    m.def("configure", &configure, "Configure the pathfinder");

    py::class_<Counter>(m, "Counter")
        .def_readonly("name", &Counter::name)
        .def_readonly("in_cnt", &Counter::in_cnt)
        .def_readonly("weak_in_cnt", &Counter::weak_in_cnt)
        .def_readonly("out_cnt", &Counter::out_cnt)
        .def_readonly("hide", &Counter::hide)
        .def_readonly("out_weaker", &Counter::out_weaker)
        .def_readonly("out_stronger", &Counter::out_stronger)
        .def_readonly("multi", &Counter::multi)
        .def_readonly("total_counter", &Counter::total_counter)
        .def_readonly("time_spent_s", &Counter::time_spent_s);

    py::class_<Node>(m, "Node")
        .def(py::init<std::string, std::string, NodeType, uint64_t, GraphInterface &>())
        .def_readonly("py_ptr", &Node::py_ptr);

    py::class_<GraphInterface>(m, "GraphInterface")
        .def(py::init<GraphInterfaceType, uint64_t, Graph &>())
        //.def_property("node", &GraphInterface::get_node,
        //              &GraphInterface::set_node)
        .def("set_node", &GraphInterface::set_node)
        .def_readonly("py_ptr", &GraphInterface::py_ptr)
        .def("make_hierarchical", &GraphInterface::make_hierarchical);

    py::class_<Link>(m, "Link")
        .def(py::init<LinkType, uint64_t, std::vector<NodeGranularType>>())
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
        .value("DIRECT_CONDITIONAL_SHALLOW", LinkType::L_DIRECT_CONDITIONAL_SHALLOW)
        .value("DIRECT_DERIVED", LinkType::L_DIRECT_DERIVED)
        .value("OTHER", LinkType::L_OTHER);

    py::enum_<NodeType>(m, "NodeType")
        .value("GENERIC", NodeType::N_GENERIC)
        .value("MODULE", NodeType::N_MODULE)
        .value("MODULEINTERFACE", NodeType::N_MODULEINTERFACE)
        .value("OTHER", NodeType::N_OTHER);
}
