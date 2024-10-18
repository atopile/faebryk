#pragma once

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
    L_DIRECT_DERIVED,
    L_OTHER,
};

struct Link {
    LinkType type;
    uint64_t py_ptr;
};

struct GraphInterface;
class Graph;

using NodeGranularType = std::string;

struct Node {
    std::string name;
    NodeGranularType granular_type;
    NodeType type;
    uint64_t py_ptr;
    GraphInterface &self_gif;

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

    std::optional<Link> is_connected(GraphInterface &to);

    std::vector<GraphInterface *> edges();

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
    bool is_uplink(GraphInterface &to) {
        return this->is_hierarchical() && to.type == this->type && !this->is_parent &&
               to.is_parent;
    }
    bool is_downlink(GraphInterface &to) {
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
    std::unordered_set<GraphInterface *> v;
    std::vector<std::tuple<GraphInterface *, GraphInterface *, Link *>> e;
    std::unordered_map<GraphInterface *, std::unordered_map<GraphInterface *, Link *>>
        e_cache = {};
    std::unordered_map<GraphInterface *, std::vector<GraphInterface *>> e_cache_simple =
        {};

  public:
    std::unordered_map<GraphInterface *, Link *> &edges(GraphInterface *v) {
        return e_cache[v];
    }

    std::vector<GraphInterface *> edges_simple(GraphInterface *v) {
        return e_cache_simple[v];
    }

    void
    add_edges(std::vector<std::tuple<GraphInterface *, GraphInterface *, Link *>> &e) {
        for (auto &edge : e) {
            auto &from = *std::get<0>(edge);
            auto &to = *std::get<1>(edge);
            auto &link = *std::get<2>(edge);
            add_edge(from, to, link);
        }
    }

    void add_edge(GraphInterface &from, GraphInterface &to, Link &link) {
        e.push_back(std::make_tuple(&from, &to, &link));
        e_cache[&from][&to] = &link;
        e_cache[&to][&from] = &link;
        e_cache_simple[&from].push_back(&to);
        e_cache_simple[&to].push_back(&from);

        // printf("add_edge: %p[%lx] -> %p[%lx]\n", &from, from.py_ptr, &to,
        //        to.py_ptr);
        if (v.insert(&from).second) {
            from.v_i = v_i++;
        }
        if (v.insert(&to).second) {
            to.v_i = v_i++;
        }
    }

    std::optional<Link> is_connected(GraphInterface &from, GraphInterface &to);
};

struct Path {
    std::vector<GraphInterface *> gifs;

    Path(std::vector<GraphInterface *> gifs)
      : gifs(gifs) {
    }
};

inline std::optional<Link> GraphInterface::is_connected(GraphInterface &to) {
    return graph.is_connected(*this, to);
}

inline std::optional<Link> Graph::is_connected(GraphInterface &from,
                                               GraphInterface &to) {
    auto out = e_cache[&from][&to];
    if (!out) {
        return {};
    }
    return *out;
}

inline std::vector<GraphInterface *> GraphInterface::edges() {
    return graph.edges_simple(this);
}