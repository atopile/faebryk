/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "util.hpp"
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/unordered_map.h>
#include <nanobind/stl/unordered_set.h>
#include <nanobind/stl/vector.h>
#include <sstream>
#include <vector>

namespace nb = nanobind;

template <typename T> using Set = std::unordered_set<T>;
template <typename K, typename V> using Map = std::unordered_map<K, V>;

class Graph;
class GraphInterface;
class GraphInterfaceHierarchical;
class GraphInterfaceSelf;
class Link;
class Node;

using GI_ref = std::shared_ptr<GraphInterface>;
using GI_ref_weak = GraphInterface *;
using Link_ref = std::shared_ptr<Link>;
using Node_ref = std::shared_ptr<Node>;

class Node {
  private:
    std::optional<nb::object> py_handle{};

  public:
    struct NodeException : public std::runtime_error {
        NodeException(Node &node, const std::string &msg)
          : std::runtime_error(msg) {
        }
    };

    struct NodeNoParent : public NodeException {
        NodeNoParent(Node &node, const std::string &msg)
          : NodeException(node, msg) {
        }
    };

  private:
    std::shared_ptr<GraphInterfaceSelf> self;
    std::shared_ptr<GraphInterfaceHierarchical> children;
    std::shared_ptr<GraphInterfaceHierarchical> parent;

  public:
    Node();
    // TODO add checks for whether this was called
    static Node_ref transfer_ownership(Node_ref node);
    Node_ref factory();

    std::shared_ptr<Graph> get_graph();
    std::shared_ptr<GraphInterfaceSelf> get_self_gif();
    std::shared_ptr<GraphInterfaceHierarchical> get_children_gif();
    std::shared_ptr<GraphInterfaceHierarchical> get_parent_gif();

    std::optional<std::pair<Node_ref, std::string>> get_parent();
    std::pair<Node_ref, std::string> get_parent_force();
    std::string get_name();
    std::vector<std::pair<Node *, std::string>> get_hierarchy();
    std::string get_full_name(bool types = false);
    std::string repr();

    std::string get_type_name();
    // TODO replace with constructor
    void set_py_handle(nb::object handle);
    std::optional<nb::object> get_py_handle();
};

class GraphInterface {
    Node_ref node{};
    std::string name{};

  protected:
    void register_graph(std::shared_ptr<GraphInterface> gi);

  public:
    GraphInterface();
    ~GraphInterface();

    std::shared_ptr<Graph> G;

    template <typename T> static std::shared_ptr<T> factory();
    std::unordered_set<GI_ref_weak> get_gif_edges();
    std::unordered_map<GI_ref_weak, Link_ref> get_edges();
    std::optional<Link_ref> is_connected(GI_ref_weak to);
    std::shared_ptr<Graph> get_graph();
    std::unordered_set<Node_ref> get_connected_nodes(std::vector<nb::type_object> types);
    void connect(GI_ref_weak other);
    void connect(GI_ref_weak other, Link_ref link);
    // TODO replace with set_node(Node_ref node, std::string name)
    void set_node(Node_ref node);
    Node_ref get_node();
    void set_name(std::string name);
    std::string get_name();
    std::string get_full_name(bool types = false);
    std::string repr();
    // force vtable, for typename
    virtual void do_stuff() {};
};

class Link {
    GI_ref_weak from;
    GI_ref_weak to;
    bool setup = false;

  protected:
    Link();
    Link(GI_ref_weak from, GI_ref_weak to);

  public:
    std::pair<GI_ref_weak, GI_ref_weak> get_connections();
    virtual void set_connections(GI_ref_weak from, GI_ref_weak to);
    bool is_setup();
};

class Graph {
    Set<GI_ref> v;
    std::vector<std::tuple<GI_ref_weak, GI_ref_weak, Link_ref>> e;
    Map<GI_ref_weak, Map<GI_ref_weak, Link_ref>> e_cache = {};
    Map<GI_ref_weak, Set<GI_ref_weak>> e_cache_simple = {};
    bool invalidated = false;

  public:
    void hold(GI_ref gi);
    void add_edge(Link_ref link);
    void remove_edge(Link_ref link);
    void merge(Graph &other);

    std::unordered_set<GI_ref_weak> get_gif_edges(GI_ref_weak from);
    std::unordered_map<GI_ref_weak, Link_ref> get_edges(GI_ref_weak from);

    Graph();
    ~Graph();

    void remove_node(GI_ref node);

    void invalidate();
    int node_count();
    int edge_count();

    std::string repr();

    // Algorithms
    std::unordered_set<Node_ref> node_projection();
    std::vector<std::pair<Node_ref, std::string>>
    nodes_by_names(std::unordered_set<std::string> names);
    std::unordered_set<GI_ref_weak>
    bfs_visit(std::function<bool(std::vector<GI_ref_weak> &, Link_ref)> filter,
              std::vector<GI_ref_weak> start);
};

template <typename T> inline std::shared_ptr<T> GraphInterface::factory() {
    static_assert(std::is_base_of<GraphInterface, T>::value,
                  "T must be a subclass of GraphInterface");
    auto gi = std::make_shared<T>();
    gi->register_graph(gi);
    return gi;
}
