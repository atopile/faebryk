/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/links.hpp"

// LinkParent implementations
void LinkParent::set_connections(GraphInterfaceHierarchical *from,
                                 GraphInterfaceHierarchical *to) {
    Link::set_connections(from, to);
    if (from->get_is_parent() && !to->get_is_parent()) {
        this->parent = from;
        this->child = to;
    } else if (!from->get_is_parent() && to->get_is_parent()) {
        this->parent = to;
        this->child = from;
    } else {
        throw std::runtime_error("invalid parent-child relationship");
    }
}

GraphInterfaceHierarchical *LinkParent::get_parent() {
    if (!this->is_setup()) {
        throw std::runtime_error("link not setup");
    }
    return this->parent;
}

GraphInterfaceHierarchical *LinkParent::get_child() {
    if (!this->is_setup()) {
        throw std::runtime_error("link not setup");
    }
    return this->child;
}

// Constructor implementations
LinkParent::LinkParent()
  : Link()
  , parent(nullptr)
  , child(nullptr) {
}

LinkParent::LinkParent(GraphInterfaceHierarchical *from, GraphInterfaceHierarchical *to)
  : Link(from, to)
  , parent(nullptr)
  , child(nullptr) {
    this->set_connections(from, to);
}

LinkNamedParent::LinkNamedParent(std::string name)
  : LinkParent()
  , name(name) {
}

LinkNamedParent::LinkNamedParent(std::string name, GraphInterfaceHierarchical *from,
                                 GraphInterfaceHierarchical *to)
  : LinkParent(from, to)
  , name(name) {
}

LinkPointer::LinkPointer()
  : Link() {
}

LinkPointer::LinkPointer(GI_ref_weak from, GI_ref_weak to)
  : Link(from, to) {
}

LinkSibling::LinkSibling()
  : LinkPointer() {
}

LinkSibling::LinkSibling(GI_ref_weak from, GI_ref_weak to)
  : LinkPointer(from, to) {
}

// LinkNamedParent implementations
std::string LinkNamedParent::get_name() {
    return this->name;
}

// LinkDirect implementations
LinkDirect::LinkDirect()
  : Link() {
}

LinkDirect::LinkDirect(GI_ref_weak from, GI_ref_weak to)
  : Link(from, to) {
}
