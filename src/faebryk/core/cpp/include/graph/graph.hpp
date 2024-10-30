/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "util.hpp"
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/unordered_map.h>
#include <nanobind/stl/unordered_set.h>
#include <sstream>
#include <vector>

namespace nb = nanobind;

template <typename T> using Set = std::unordered_set<T>;
template <typename K, typename V> using Map = std::unordered_map<K, V>;

class Graph;
class GraphInterface;
class Link;

class Node {};

using GI_ref = std::shared_ptr<GraphInterface>;
using GI_ref_weak = GraphInterface *;
using Link_ref = std::shared_ptr<Link>;

// TODO: think about how to fix the cyclic shared_ptrs GraphInterface <-> Graph
// we want to keep both objects alive as long as either is in use in python
// https://nanobind.readthedocs.io/en/latest/typeslots.html#cyclic-garbage-collection

class GraphInterface {
  protected:
    void register_graph(std::shared_ptr<GraphInterface> gi);

  public:
    GraphInterface();

    std::shared_ptr<Graph> G;

    ~GraphInterface();

    static std::shared_ptr<GraphInterface> factory() {
        auto gi = std::make_shared<GraphInterface>();
        gi->register_graph(gi);
        return gi;
    }

    // Graph stuff
    std::unordered_set<GI_ref_weak> get_gif_edges();
    std::unordered_map<GI_ref_weak, Link_ref> get_edges();

    std::shared_ptr<Graph> get_graph() {
        return this->G;
    }

    void connect(GI_ref_weak other);
    void connect(GI_ref_weak other, Link_ref link);

    // TODO remove, gives class vtable
    virtual void do_stuff() {};

    std::string repr() {
        std::stringstream ss;
        ss << "<" << get_type_name(this) << " at "
           << this
           //<< " #" << this->shared_from_this().use_count()
           << ">";
        return ss.str();
    }
};

class Link {
    GI_ref_weak from;
    GI_ref_weak to;
    bool setup = false;

  protected:
    Link()
      : from(nullptr)
      , to(nullptr)
      , setup(false) {
    }
    Link(GI_ref_weak from, GI_ref_weak to)
      : from(from)
      , to(to)
      , setup(true) {
    }

  public:
    std::pair<GI_ref_weak, GI_ref_weak> get_connections() {
        if (!this->setup) {
            throw std::runtime_error("link not setup");
        }
        return {this->from, this->to};
    }

    virtual void set_connections(GI_ref_weak from, GI_ref_weak to) {
        this->from = from;
        this->to = to;
        this->setup = true;
    }

    bool is_setup() {
        return this->setup;
    }
};

/**
 * @brief Represents a direct link between two interfaces of the same type
 *
 */
class LinkDirect : public Link {
  public:
    LinkDirect()
      : Link() {
    }
    LinkDirect(GI_ref_weak from, GI_ref_weak to)
      : Link(from, to) {
    }
};

#include "links.hpp"

class Graph {
    Set<GI_ref> v;
    std::vector<std::tuple<GI_ref_weak, GI_ref_weak, Link_ref>> e;
    Map<GI_ref_weak, Map<GI_ref_weak, Link_ref>> e_cache = {};
    Map<GI_ref_weak, Set<GI_ref_weak>> e_cache_simple = {};
    bool invalidated = false;

  public:
    void hold(GI_ref gi) {
        this->v.insert(gi);
    }

    void add_edge(Link_ref link) {
        auto [from, to] = link->get_connections();

        // printf("add_edge from %s to %s\n", from->repr().c_str(), to->repr().c_str());

        if (from->G.get() != this || to->G.get() != this) {
            Graph *G_target = this;
            Graph *G_source;
            if (from->G.get() == G_target) {
                G_source = to->G.get();
            } else if (to->G.get() == G_target) {
                G_source = from->G.get();
            } else {
                throw std::runtime_error("neither node in graph");
            }
            // printf("Merging graphs: %p ---> %p\n", G_source, G_target);

            assert(G_source->v.size() > 0);
            // make shared_ptr, while in scope
            auto G_source_hold = (*G_source->v.begin())->G;

            for (auto &v : G_source->v) {
                v->G = from->G;
            }
            G_target->merge(*G_source);
            G_source->invalidate();
        }

        e_cache_simple[from].insert(to);
        e_cache_simple[to].insert(from);
        e_cache[from][to] = link;
        e_cache[to][from] = link;
        e.push_back(std::make_tuple(from, to, link));
    }

    void merge(Graph &other) {
        this->v.merge(other.v);
        this->e.insert(this->e.end(), other.e.begin(), other.e.end());
        this->e_cache.merge(other.e_cache);
        this->e_cache_simple.merge(other.e_cache_simple);
    }

    std::unordered_set<GI_ref_weak> get_gif_edges(GI_ref_weak from) {
        return this->e_cache_simple[from];
    }

    std::unordered_map<GI_ref_weak, Link_ref> get_edges(GI_ref_weak from) {
        return this->e_cache[from];
    }

    Graph() {
    }

    ~Graph() {
        if (!this->invalidated) {
            printf("WARNING: graph not invalidated\n");
            // throw std::runtime_error("graph not invalidated");
        }
    }

    void remove_node(GI_ref node) {
        // basically never happens
        auto node_ptr = node.get();
        // v
        this->v.erase(node);
        // nb::dec_ref(node);

        // e_cache_simple
        for (auto &[from, tos] : this->e_cache_simple) {
            tos.erase(node_ptr);
        }
        this->e_cache_simple.erase(node_ptr);

        // e_cache
        for (auto &[to, link] : this->e_cache[node_ptr]) {
            this->e_cache[to].erase(node_ptr);
        }
        this->e_cache.erase(node_ptr);

        // e
        std::erase_if(this->e, [node_ptr](const auto &edge) {
            return std::get<0>(edge) == node_ptr || std::get<1>(edge) == node_ptr;
        });
    }

    void check_destruct() {
    }

    void invalidate() {
        this->invalidated = true;
        this->v.clear();
    }

    int node_count() {
        return this->v.size();
    }

    int edge_count() {
        return this->e.size();
    }

    std::string repr() {
        std::stringstream ss;
        ss << "<Graph[V:" << this->node_count() << ", E:" << this->edge_count()
           << "] at " << this << ">";
        return ss.str();
    }
};

Set<GI_ref_weak> GraphInterface::get_gif_edges() {
    return this->G->get_gif_edges(this);
}

std::unordered_map<GI_ref_weak, Link_ref> GraphInterface::get_edges() {
    return this->G->get_edges(this);
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

GraphInterface::~GraphInterface() {
}

GraphInterface::GraphInterface()
  : G(std::make_shared<Graph>()) {
}

void GraphInterface::register_graph(std::shared_ptr<GraphInterface> gi) {
    this->G->hold(gi);
}
