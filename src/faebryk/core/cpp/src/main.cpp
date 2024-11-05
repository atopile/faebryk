/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graph.hpp"
#include "graph/graphinterfaces.hpp"
#include "graph/links.hpp"
#include "nano.hpp"
#include <nanobind/nanobind.h>

// check if c++20 is used
#if __cplusplus < 202002L
#error "C++20 is required"
#endif

#if EDITABLE
#define PYMOD(m) NB_MODULE(faebryk_core_cpp_editable, m)
#warning "EDITABLE"
#else
#define PYMOD(m) NB_MODULE(faebryk_core_cpp, m)
#endif

// #include <nanobind/nb_types.h>

namespace nb = nanobind;
using namespace nb::literals;

// -------------------------------------------------------------------------------------

int add(int i, int j) {
    return i + j;
}

int call_python_function(std::function<int()> func) {
    auto out = func();
    printf("%d\n", out);
    return out;
}

PYMOD(m) {
    m.doc() = "faebryk core c++ module";

    m.def("add", &add, "i"_a, "j"_a = 1, "A function that adds two numbers");
    m.def("call_python_function", &call_python_function, "func"_a);
    m.def("set_leak_warnings", &nb::set_leak_warnings, "value"_a);

    // Graph
    using GI = GraphInterface;

    FACTORY(nb::class_<GI>(m, "GraphInterface")
                .def("__repr__", &GI::repr)
                .def("get_graph", &GI::get_graph)
                .def("get_gif_edges", &GI::get_gif_edges)
                .def_prop_ro("edges", &GI::get_edges)
                .def_prop_rw("node", &GI::get_node, &GI::set_node)
                .def("is_connected", &GI::is_connected)
                .def_prop_rw("name", &GI::get_name, &GI::set_name)
                .def("connect", nb::overload_cast<GI_ref_weak>(&GI::connect))
                .def("connect", nb::overload_cast<GI_ref_weak, Link_ref>(&GI::connect)),
            &GraphInterface::factory);

    nb::class_<Graph>(m, "Graph")
        .def(nb::init<>())
        .def("get_edges", &Graph::get_edges)
        .def("invalidate", &Graph::invalidate)
        .def_prop_ro("node_count", &Graph::node_count)
        .def_prop_ro("edge_count", &Graph::edge_count)
        .def("node_projection", &Graph::node_projection)
        .def("nodes_by_names", &Graph::nodes_by_names)
        .def("bfs_visit", &Graph::bfs_visit)
        .def("__repr__", &Graph::repr);

    // Graph interfaces
    FACTORY((nb::class_<GraphInterfaceSelf, GI>(m, "GraphInterfaceSelf")),
            &GraphInterfaceSelf::factory);

    FACTORY((nb::class_<GraphInterfaceReference, GI>(m, "GraphInterfaceReference")),
            &GraphInterfaceReference::factory);

    FACTORY(
        (nb::class_<GraphInterfaceHierarchical, GI>(m, "GraphInterfaceHierarchical")
             .def("get_parent", &GraphInterfaceHierarchical::get_parent)
             .def("get_children", &GraphInterfaceHierarchical::get_children)
             .def_prop_ro("is_parent", &GraphInterfaceHierarchical::get_is_parent)
             .def("disconnect_parent", &GraphInterfaceHierarchical::disconnect_parent)),
        &GraphInterfaceHierarchical::factory, "is_parent"_a);

    // Links
    nb::class_<Link>(m, "Link");
    nb::class_<LinkParent, Link>(m, "LinkParent").def(nb::init<>());
    nb::class_<LinkNamedParent, LinkParent>(m, "LinkNamedParent")
        .def(nb::init<std::string>());
    nb::class_<LinkDirect, Link>(m, "LinkDirect").def(nb::init<>());
    nb::class_<LinkPointer, Link>(m, "LinkPointer").def(nb::init<>());
    nb::class_<LinkSibling, LinkPointer>(m, "LinkSibling").def(nb::init<>());
    nb::class_<LinkDirectConditional, LinkDirect>(m, "LinkDirectConditional")
        .def(nb::init<LinkDirectConditional::FilterF>());

    // Node
    nb::class_<Node>(m, "Node")
        .def(nb::init<>())
        .def_static("transfer_ownership", &Node::transfer_ownership)
        .def("get_graph", &Node::get_graph)
        .def_prop_ro("self_gif", &Node::get_self_gif)
        .def_prop_ro("children", &Node::get_children_gif)
        .def_prop_ro("parent", &Node::get_parent_gif)
        .def("get_parent", &Node::get_parent)
        .def("get_parent_force", &Node::get_parent_force)
        .def("get_name", &Node::get_name)
        .def("get_hierarchy", &Node::get_hierarchy)
        .def("get_full_name", &Node::get_full_name, "types"_a = false)
        .def("__repr__", &Node::repr);

    nb::exception<Node::NodeException>(m, "NodeException");
    nb::exception<Node::NodeNoParent>(m, "NodeNoParent");
}
