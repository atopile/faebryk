/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graph.hpp"
#include "graphinterfaces.hpp"
#include "links.hpp"
#include "nano.hpp"
#include <nanobind/nanobind.h>

// check if c++20 is used
#if __cplusplus < 202002L
#error "C++20 is required"
#endif

namespace nb = nanobind;
using namespace nb::literals;

#if EDITABLE
#define PYMOD(m) NB_MODULE(faebryk_core_cpp_editable, m)
#warning "EDITABLE"
#else
#define PYMOD(m) NB_MODULE(faebryk_core_cpp, m)
#endif

// -------------------------------------------------------------------------------------

int add(int i, int j) {
    return i + j;
}

PYMOD(m) {
    m.doc() = "faebryk core c++ module";

    m.def("add", &add, "i"_a, "j"_a = 1, "A function that adds two numbers");

    // Graph
    using GI = GraphInterface;

    FACTORY(nb::class_<GI>(m, "GraphInterface")
                .def("__repr__", &GI::repr)
                .def("get_graph", &GI::get_graph)
                .def("get_edges", &GI::get_edges)
                .def("connect", nb::overload_cast<GI_ref_weak>(&GI::connect))
                .def("connect", nb::overload_cast<GI_ref_weak, Link_ref>(&GI::connect))
                .def("connect",
                     nb::overload_cast<GI_ref_weak, nb::type_object>(&GI::connect)),
            &GraphInterface::factory);

    nb::class_<Link>(m, "Link");

    nb::class_<Graph>(m, "Graph")
        .def(nb::init<>())
        .def("get_edges", &Graph::get_edges)
        .def("invalidate", &Graph::invalidate)
        .def_prop_ro("node_count", &Graph::node_count)
        .def_prop_ro("edge_count", &Graph::edge_count)
        .def("__repr__", &Graph::repr);

    // Graph interfaces
    FACTORY((nb::class_<GraphInterfaceSelf, GI>(m, "GraphInterfaceSelf")),
            &GraphInterfaceSelf::factory);

    FACTORY((nb::class_<GraphInterfaceReference, GI>(m, "GraphInterfaceReference")),
            &GraphInterfaceReference::factory);

    FACTORY(
        (nb::class_<GraphInterfaceHierarchical, GI>(m, "GraphInterfaceHierarchical")),
        &GraphInterfaceHierarchical::factory, "is_parent"_a);

    // Links
    nb::class_<LinkParent>(m, "LinkParent");
    nb::class_<LinkNamedParent>(m, "LinkNamedParent");
    nb::class_<LinkDirect>(m, "LinkDirect");
    nb::class_<LinkPointer>(m, "LinkPointer");
    nb::class_<LinkSibling>(m, "LinkSibling");
}
