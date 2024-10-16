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

struct Node {
    std::string name;
    std::string type_name;
    NodeType type;
    uint64_t py_ptr;
    GraphInterface &self_gif;

    bool is_instance(NodeType type) const {
        return this->type == type;
    }
};

struct GraphInterface {
    Node *node = nullptr;
    GraphInterfaceType type;
    uint64_t py_ptr;
    Graph &graph;

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
};

class Graph {

  public:
    std::unordered_set<GraphInterface *> v;
    std::vector<std::tuple<GraphInterface *, GraphInterface *, Link *>> e;
    std::unordered_map<GraphInterface *,
                       std::unordered_map<GraphInterface *, Link *>>
        e_cache = {};

  public:
    std::unordered_map<GraphInterface *, Link *> &edges(GraphInterface *v) {
        return e_cache[v];
    }

    void add_edges(
        std::vector<std::tuple<GraphInterface *, GraphInterface *, Link *>>
            &e) {
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

        // printf("add_edge: %p[%lx] -> %p[%lx]\n", &from, from.py_ptr, &to,
        //        to.py_ptr);
        v.insert(&from);
        v.insert(&to);
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
    auto edges = graph.edges(this);
    std::cout << "edges: " << edges.size() << std::endl;
    // get keys from unordered_map
    std::vector<GraphInterface *> keys;
    for (auto &edge : edges) {
        keys.push_back(edge.first);
    }
    return keys;
}