/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graph.hpp"
#include "graph/links.hpp"

Node::Node()
  : self(GraphInterfaceSelf::factory<GraphInterfaceSelf>())
  , children(GraphInterfaceHierarchical::factory<GraphInterfaceHierarchical>(true))
  , parent(GraphInterfaceHierarchical::factory<GraphInterfaceHierarchical>(false)) {

    this->self->set_name("self");

    this->children->set_name("children");
    this->children->connect(this->self.get(), std::make_shared<LinkDirect>());

    this->parent->set_name("parent");
    this->parent->connect(this->self.get(), std::make_shared<LinkDirect>());
}

Node_ref Node::factory() {
    auto node = std::make_shared<Node>();
    return transfer_ownership(node);
}

Node_ref Node::transfer_ownership(Node_ref node) {
    node->self->set_node(node);
    node->children->set_node(node);
    node->parent->set_node(node);
    return node;
}

std::shared_ptr<Graph> Node::get_graph() {
    return this->self->get_graph();
}

std::shared_ptr<GraphInterfaceSelf> Node::get_self_gif() {
    return this->self;
}

std::shared_ptr<GraphInterfaceHierarchical> Node::get_children_gif() {
    return this->children;
}

std::shared_ptr<GraphInterfaceHierarchical> Node::get_parent_gif() {
    return this->parent;
}

std::optional<std::pair<Node_ref, std::string>> Node::get_parent() {
    return this->parent->get_parent();
}

std::pair<Node_ref, std::string> Node::get_parent_force() {
    auto p = this->get_parent();
    if (!p) {
        throw NodeNoParent(*this, __func__);
    }
    return *p;
}

std::string Node::get_name() {
    return this->get_parent_force().second;
}

std::vector<std::pair<Node *, std::string>> Node::get_hierarchy() {
    auto p = this->get_parent();
    if (!p) {
        return std::vector{std::make_pair(this, std::string("*"))};
    }
    auto [parent, name] = *p;
    auto parent_hierarchy = parent->get_hierarchy();
    parent_hierarchy.push_back(std::make_pair(this, name));
    return parent_hierarchy;
}

std::string Node::get_full_name(bool types) {
    std::stringstream ss;
    auto p = this->get_parent();
    if (p) {
        auto [parent, name] = *p;
        auto parent_hierarchy = parent->get_full_name(types);
        ss << parent_hierarchy << "." << name;
    } else {
        ss << "*";
    }
    if (types) {
        ss << "|" << this->get_type_name();
    }
    return ss.str();
}

std::string Node::repr() {
    std::stringstream ss;
    ss << "<" << this->get_full_name(true) << ">";
    return ss.str();
}

std::string Node::get_type_name() {
    if (this->py_handle.has_value()) {
        auto out = std::string(
            nb::repr(this->py_handle.value().type().attr("__name__")).c_str());
        // format : 'ClassName'
        // extract ClassName
        // remove quotes
        auto pos = out.find_first_of('\'');
        if (pos != std::string::npos) {
            out = out.substr(pos + 1, out.size() - 2);
        }
        return out;
    }
    return util::get_type_name(this);
}

void Node::set_py_handle(nb::object handle) {
    if (this->py_handle.has_value()) {
        throw std::runtime_error("py_handle already set");
    }
    this->py_handle = handle;
}

std::optional<nb::object> Node::get_py_handle() {
    return this->py_handle;
}
