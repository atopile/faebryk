/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graphinterfaces.hpp"
#include "graph/links.hpp"

std::shared_ptr<GraphInterfaceSelf> GraphInterfaceSelf::factory() {
    auto gi = std::make_shared<GraphInterfaceSelf>();
    gi->register_graph(gi);
    return gi;
}

GraphInterfaceSelf::GraphInterfaceSelf()
  : GraphInterface() {
}

std::shared_ptr<GraphInterfaceHierarchical>
GraphInterfaceHierarchical::factory(bool is_parent) {
    auto gi = std::make_shared<GraphInterfaceHierarchical>(is_parent);
    gi->register_graph(gi);
    return gi;
}

bool GraphInterfaceHierarchical::get_is_parent() {
    return this->is_parent;
}

std::vector<std::pair<Node_ref, std::string>>
GraphInterfaceHierarchical::get_children() {
    assert(this->is_parent);

    auto edges = this->get_edges();
    std::vector<std::pair<Node_ref, std::string>> children;
    for (auto [to, link] : edges) {
        if (auto named_link = dynamic_cast<LinkNamedParent *>(link.get())) {
            children.push_back(std::make_pair(to->get_node(), named_link->get_name()));
        }
    }
    return children;
}

std::optional<std::pair<Node_ref, std::string>>
GraphInterfaceHierarchical::get_parent() {
    assert(!this->is_parent);

    auto edges = this->get_edges();
    for (auto [to, link] : edges) {
        if (auto named_link = dynamic_cast<LinkNamedParent *>(link.get())) {
            return std::make_pair(to->get_node(), named_link->get_name());
        }
    }
    return std::nullopt;
}

GraphInterfaceHierarchical::GraphInterfaceHierarchical(bool is_parent)
  : GraphInterface()
  , is_parent(is_parent) {
}

std::shared_ptr<GraphInterfaceReference> GraphInterfaceReference::factory() {
    auto gi = std::make_shared<GraphInterfaceReference>();
    gi->register_graph(gi);
    return gi;
}

GraphInterfaceReference::GraphInterfaceReference()
  : GraphInterface() {
}

GraphInterfaceSelf *GraphInterfaceReference::get_referenced_gif() {
    auto edges = this->get_edges();
    for (auto [to, link] : edges) {
        if (auto pointer_link = dynamic_cast<LinkPointer *>(link.get())) {
            return pointer_link->get_pointee();
        }
    }
    throw UnboundError("Reference is not bound");
}

Node_ref GraphInterfaceReference::get_reference() {
    return this->get_referenced_gif()->get_node();
}
