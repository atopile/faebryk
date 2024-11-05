/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graphinterfaces.hpp"
#include "graph/links.hpp"

std::shared_ptr<Graph> GraphInterface::get_graph() {
    return this->G;
}

void GraphInterface::set_node(Node_ref node) {
    assert(!this->node);
    this->node = node;
}

Node_ref GraphInterface::get_node() {
    assert(this->node);
    return this->node;
}

void GraphInterface::set_name(std::string name) {
    assert(this->name.empty());
    this->name = name;
}

std::string GraphInterface::get_name() {
    return this->name;
}

std::string GraphInterface::get_full_name(bool types) {
    assert(this->node);

    std::stringstream ss;
    ss << this->get_node()->get_full_name(types) << "." << this->name;
    if (types) {
        ss << "|" << util::get_type_name(this) << "|";
    }
    return ss.str();
}

std::string GraphInterface::repr() {
    std::stringstream ss;
    ss << "<" << util::get_type_name(this) << " at " << this << ">";
    return ss.str();
}

GraphInterface::~GraphInterface() {
}

GraphInterface::GraphInterface()
  : G(std::make_shared<Graph>()) {
}

void GraphInterface::connect(GI_ref_weak other) {
    auto link = std::make_shared<LinkDirect>(this, other);
    this->G->add_edge(link);
}

void GraphInterface::connect(GI_ref_weak other, Link_ref link) {
    if (link->is_setup()) {
        throw std::runtime_error("link already setup");
    }
    link->set_connections(this, other);
    this->G->add_edge(link);
}

void GraphInterface::register_graph(std::shared_ptr<GraphInterface> gi) {
    this->G->hold(gi);
}

std::optional<Link_ref> GraphInterface::is_connected(GI_ref_weak to) {
    auto edges = this->get_edges();
    auto edge = edges.find(to);
    if (edge == edges.end()) {
        return {};
    }
    return edge->second;
}

Set<GI_ref_weak> GraphInterface::get_gif_edges() {
    return this->G->get_gif_edges(this);
}

std::unordered_map<GI_ref_weak, Link_ref> GraphInterface::get_edges() {
    return this->G->get_edges(this);
}
