#pragma once

#include "util.hpp"
#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

enum NodeType {
    N_GENERIC,
    N_MODULE,
    N_MODULEINTERFACE,
    N_OTHER,
};
enum GraphInterfaceType {
    G_GENERIC,
    G_HIERARCHICAL,
    G_SELF,
    G_HIERARCHICAL_NODE,
    G_HIERARCHICAL_MODULE_SPECIAL,
    G_MODULE_CONNECTION,
    G_OTHER,
};
enum LinkType {
    L_GENERIC,
    L_SIBLING,
    L_PARENT,
    L_NAMED_PARENT,
    L_DIRECT,
    L_DIRECT_CONDITIONAL,
    L_DIRECT_CONDITIONAL_SHALLOW,
    L_DIRECT_DERIVED,
    L_OTHER,
};

using NodeGranularType = std::string;
struct GraphInterface;
class Graph;
class Node;

struct Link {
    LinkType type;
    uint64_t py_ptr;

    // LinkDirectConditionalShallow
    std::vector<NodeGranularType> shallow_filter;
    bool is_filtered(const Node &node) const;

    // LinkDirectConditional
    std::optional<std::function<bool(const std::vector<const GraphInterface *> &)>>
        filter;
};

struct Node {
    std::string name;
    NodeGranularType granular_type;
    NodeType type;
    uint64_t py_ptr;
    const GraphInterface &self_gif;

    bool is_instance(NodeType type) const {
        return this->type == type;
    }

    bool operator==(const Node &other) const {
        return this->py_ptr == other.py_ptr;
    }
};

struct GraphInterface {
    Node *node = nullptr;
    GraphInterfaceType type;
    uint64_t py_ptr;
    Graph &graph;
    size_t v_i = 0;

    GraphInterface(GraphInterfaceType type, uint64_t py_ptr, Graph &graph)
      : type(type)
      , py_ptr(py_ptr)
      , graph(graph) {
    }

    void set_node(Node *node) {
        assert(node != nullptr);
        this->node = node;
    }
    Node get_node() const {
        assert(node != nullptr);
        return *node;
    }

    bool is_instance(GraphInterfaceType type) const {
        return this->type == type;
    }

    std::vector<const GraphInterface *> edges() const;

    std::optional<const Link *> is_connected(const GraphInterface &to) const;

    // GraphInterfaceHierarchical stuff
    bool is_parent = false;
    std::optional<std::string> parent_name = {};
    void make_hierarchical(bool is_parent, std::string parent_name) {
        this->is_parent = is_parent;
        if (!is_parent) {
            this->parent_name = parent_name;
        }
    }
    bool is_hierarchical() const {
        return this->type == GraphInterfaceType::G_HIERARCHICAL ||
               this->type == GraphInterfaceType::G_HIERARCHICAL_NODE;
    }
    bool is_uplink(const GraphInterface &to) const {
        return this->is_hierarchical() && to.type == this->type && !this->is_parent &&
               to.is_parent;
    }
    bool is_downlink(const GraphInterface &to) const {
        return this->is_hierarchical() && to.type == this->type && this->is_parent &&
               !to.is_parent;
    }

    // override equality
    bool operator==(const GraphInterface &other) const {
        return this->py_ptr == other.py_ptr;
    }
};

class Graph {
    size_t v_i = 0;

  public:
    std::unordered_set<const GraphInterface *> v;
    std::vector<std::tuple<const GraphInterface *, const GraphInterface *, Link *>> e;
    std::unordered_map<const GraphInterface *,
                       std::unordered_map<const GraphInterface *, const Link *>>
        e_cache = {};
    std::unordered_map<const GraphInterface *, std::vector<const GraphInterface *>>
        e_cache_simple = {};

  public:
    std::vector<const GraphInterface *> edges_simple(const GraphInterface *v) const {
        // Never should reach a GIF that has no edges
        auto edges = e_cache_simple.find(v);
        assert(edges != e_cache_simple.end());
        return edges->second;
    }

    void
    add_edges(std::vector<std::tuple<GraphInterface &, GraphInterface &, Link &>> &e) {
        for (auto &edge : e) {
            auto &from = std::get<0>(edge);
            auto &to = std::get<1>(edge);
            auto &link = std::get<2>(edge);
            add_edge(from, to, link);
        }
    }

    void add_edge(GraphInterface &from, GraphInterface &to, Link &link) {
        e.push_back(std::make_tuple(&from, &to, &link));
        e_cache[&from][&to] = &link;
        e_cache[&to][&from] = &link;
        e_cache_simple[&from].push_back(&to);
        e_cache_simple[&to].push_back(&from);

        if (v.insert(&from).second) {
            from.v_i = v_i++;
        }
        if (v.insert(&to).second) {
            to.v_i = v_i++;
        }
    }

    std::optional<const Link *> is_connected(const GraphInterface &from,
                                             const GraphInterface &to) const;
};

struct Path {
    std::vector<const GraphInterface *> gifs;

    Path(std::vector<const GraphInterface *> gifs)
      : gifs(gifs) {
    }
};

inline std::optional<const Link *>
GraphInterface::is_connected(const GraphInterface &to) const {
    return graph.is_connected(*this, to);
}

inline std::optional<const Link *> Graph::is_connected(const GraphInterface &from,
                                                       const GraphInterface &to) const {
    auto edges = e_cache.find(&from);
    if (edges == e_cache.end()) {
        return {};
    }
    auto edge = edges->second.find(&to);
    if (edge == edges->second.end()) {
        return {};
    }
    auto &link = edge->second;
    return link;
}

inline std::vector<const GraphInterface *> GraphInterface::edges() const {
    return graph.edges_simple(this);
}

inline bool Link::is_filtered(const Node &node) const {
    return std::find(shallow_filter.begin(), shallow_filter.end(), node.granular_type) !=
           shallow_filter.end();
}
