/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "graph/graph.hpp"
#include <optional>
#include <string>
#include <tuple>
#include <vector>

using Link_weak_ref = Link *;

struct Edge {
    /*const*/ GI_ref_weak from;
    /*const*/ GI_ref_weak to;
};

using TriEdge = std::tuple</*const*/ GI_ref_weak, /*const*/ GI_ref_weak,
                           /*const*/ GI_ref_weak>;

struct PathStackElement {
    Node::Type parent_type;
    Node::Type child_type;
    /*const*/ GI_ref_weak parent_gif;
    std::string name;
    bool up;

    std::string str() /*const*/;
};

struct UnresolvedStackElement {
    PathStackElement elem;
    bool promise;

    bool match(PathStackElement &other);
    std::string str() /*const*/;
};

using PathStack = std::vector<PathStackElement>;
using UnresolvedStack = std::vector<UnresolvedStackElement>;

struct PathData {
    UnresolvedStack unresolved_stack;
    PathStack promise_stack;
};

class BFSPath {
    std::vector</*const*/ GI_ref_weak> path;
    std::shared_ptr<PathData> path_data;

  public:
    double confidence = 1.0;
    bool filtered = false;
    bool stop = false;

    BFSPath(/*const*/ GI_ref_weak path_head);
    BFSPath(/*const*/ BFSPath &other);
    BFSPath(/*const*/ BFSPath &other, /*const*/ GI_ref_weak new_head);
    BFSPath(BFSPath &&other);

    PathData &get_path_data_mut();
    PathData &get_path_data() /*const*/;
    bool strong() /*const*/;
    /*const*/ Link_weak_ref get_link(Edge edge) /*const*/;
    std::optional<Edge> last_edge() /*const*/;
    std::optional<TriEdge> last_tri_edge() /*const*/;
    BFSPath operator+(/*const*/ GI_ref_weak gif);
    /*const*/ GI_ref_weak last() /*const*/;
    /*const*/ GI_ref_weak first() /*const*/;
    /*const*/ GI_ref_weak operator[](int idx) /*const*/;
    size_t size() /*const*/;
    bool contains(/*const*/ GI_ref_weak gif) /*const*/;
    void iterate_edges(std::function<bool(Edge &)> visitor) /*const*/;
    /*const*/ std::vector</*const*/ GI_ref_weak> &get_path() /*const*/;
    size_t index(/*const*/ GI_ref_weak gif) /*const*/;
};

void bfs_visit(/*const*/ GI_ref_weak root, std::function<void(BFSPath &)> visitor);
