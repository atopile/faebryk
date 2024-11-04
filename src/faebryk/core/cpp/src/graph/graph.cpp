/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "graph/graph.hpp"
#include "graph/links.hpp"
#include <queue>

Graph::Graph() {
}

Graph::~Graph() {
    if (!this->invalidated) {
        printf("WARNING: graph not invalidated\n");
    }
}

void Graph::hold(GI_ref gi) {
    this->v.insert(gi);
}

void Graph::add_edge(Link_ref link) {
    auto [from, to] = link->get_connections();

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

        assert(G_source->v.size() > 0);
        auto G_source_hold = (*G_source->v.begin())->G;

        for (auto &v : G_source->v) {
            v->G = from->G;
        }
        G_target->merge(*G_source);
        G_source->invalidate();
    }

    // remove existing link
    if (this->e_cache_simple[from].contains(to)) {
        this->remove_edge(this->e_cache[from][to]);
    }

    e_cache_simple[from].insert(to);
    e_cache_simple[to].insert(from);
    e_cache[from][to] = link;
    e_cache[to][from] = link;
    e.push_back(std::make_tuple(from, to, link));
}

void Graph::remove_edge(Link_ref link) {
    auto [from, to] = link->get_connections();
    if (!this->e_cache_simple[from].contains(to)) {
        return;
    }
    if (this->e_cache[from][to] != link) {
        throw std::runtime_error("link not in graph");
    }
    this->e_cache_simple[from].erase(to);
    this->e_cache[from].erase(to);
    this->e_cache[to].erase(from);
    std::erase_if(this->e, [link](const auto &edge) {
        return std::get<2>(edge) == link;
    });

    // TODO
    if (this->e_cache_simple[from].empty()) {
        //     this->remove_node(from);
    }
    if (this->e_cache_simple[to].empty()) {
        //     this->remove_node(to);
    }
}

void Graph::merge(Graph &other) {
    this->v.merge(other.v);
    this->e.insert(this->e.end(), other.e.begin(), other.e.end());
    this->e_cache.merge(other.e_cache);
    this->e_cache_simple.merge(other.e_cache_simple);
}

std::unordered_set<GI_ref_weak> Graph::get_gif_edges(GI_ref_weak from) {
    return this->e_cache_simple[from];
}

std::unordered_map<GI_ref_weak, Link_ref> Graph::get_edges(GI_ref_weak from) {
    return this->e_cache[from];
}

void Graph::remove_node(GI_ref node) {
    auto node_ptr = node.get();
    this->v.erase(node);

    // TODO remove G ref from Gif

    for (auto &[from, tos] : this->e_cache_simple) {
        tos.erase(node_ptr);
    }
    this->e_cache_simple.erase(node_ptr);

    for (auto &[to, link] : this->e_cache[node_ptr]) {
        this->e_cache[to].erase(node_ptr);
    }
    this->e_cache.erase(node_ptr);

    std::erase_if(this->e, [node_ptr](const auto &edge) {
        return std::get<0>(edge) == node_ptr || std::get<1>(edge) == node_ptr;
    });
}

void Graph::invalidate() {
    this->invalidated = true;
    this->v.clear();
}

int Graph::node_count() {
    return this->v.size();
}

int Graph::edge_count() {
    return this->e.size();
}

std::string Graph::repr() {
    std::stringstream ss;
    ss << "<Graph[V:" << this->node_count() << ", E:" << this->edge_count() << "] at "
       << this << ">";
    return ss.str();
}

// Algorithms --------------------------------------------------------------------------

std::unordered_set<Node_ref> Graph::node_projection() {
    std::unordered_set<Node_ref> nodes;
    for (auto &gif : this->v) {
        if (auto self_gif = dynamic_cast<GraphInterfaceSelf *>(gif.get())) {
            auto node = self_gif->get_node();
            assert(node);
            nodes.insert(node);
        }
    }
    return nodes;
}

std::vector<std::pair<Node_ref, std::string>>
Graph::nodes_by_names(std::unordered_set<std::string> names) {
    std::vector<std::pair<Node_ref, std::string>> nodes;
    for (auto &node : this->node_projection()) {
        auto full_name = node->get_full_name();
        if (names.contains(full_name)) {
            nodes.push_back({node, full_name});
        }
    }
    return nodes;
}

std::unordered_set<GI_ref_weak>
Graph::bfs_visit(std::function<bool(std::vector<GI_ref_weak> &, Link_ref)> filter,
                 std::vector<GI_ref_weak> start) {
    std::unordered_set<GI_ref_weak> visited;
    std::queue<std::vector<GI_ref_weak>> queue;
    queue.push(start);

    while (!queue.empty()) {
        auto path = queue.front();
        queue.pop();

        auto current = path.back();

        for (auto &[next, link] : this->e_cache[current]) {
            if (visited.contains(next)) {
                continue;
            }

            std::vector<GI_ref_weak> next_path(path);
            next_path.push_back(next);

            if (filter(next_path, link)) {
                queue.push(next_path);
                visited.insert(next);
            }
        }
    }

    return visited;
}
