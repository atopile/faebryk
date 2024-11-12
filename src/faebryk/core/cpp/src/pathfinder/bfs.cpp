/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "pathfinder/bfs.hpp"
#include "perf.hpp"
#include <deque>
#include <sstream>

std::string Edge::str() const {
    std::stringstream ss;
    ss << from->get_full_name(false) << "->" << to->get_full_name(false);
    return ss.str();
}

std::string PathStackElement::str() /*const*/ {
    std::stringstream ss;
    if (up) {
        ss << child_type.get_name() << "->" << parent_type.get_name() << "." << name;
    } else {
        ss << parent_type.get_name() << "." << name << "->" << child_type.get_name();
    }
    return ss.str();
}

bool UnresolvedStackElement::match(PathStackElement &other) {
    return elem.parent_type == other.parent_type &&
           elem.child_type == other.child_type && elem.name == other.name &&
           elem.up != other.up;
}

std::string UnresolvedStackElement::str() /*const*/ {
    std::stringstream ss;
    ss << elem.str();
    if (split) {
        ss << " split";
    }
    return ss.str();
}

// BFSPath implementations
BFSPath::BFSPath(/*const*/ GI_ref_weak path_head)
  : Path(path_head)
  , path_data(std::make_shared<PathData>()) {
}

BFSPath::BFSPath(const BFSPath &other)
  : Path(other)
  , path_data(std::make_shared<PathData>(*other.path_data))
  , confidence(other.confidence)
  , filtered(other.filtered)
  , stop(other.stop) {
}

BFSPath::BFSPath(const BFSPath &other, /*const*/ GI_ref_weak new_head)
  : Path(other)
  , path_data(other.path_data)
  , confidence(other.confidence)
  , filtered(other.filtered)
  , stop(other.stop) {
    path.push_back(new_head);
    assert(!other.filtered);
}

BFSPath::BFSPath(BFSPath &&other)
  : Path(std::move(other))
  , path_data(std::move(other.path_data))
  , confidence(other.confidence)
  , filtered(other.filtered)
  , stop(other.stop) {
}

BFSPath BFSPath::operator+(/*const*/ GI_ref_weak gif) {
    return BFSPath(*this, gif);
}

PathData &BFSPath::get_path_data_mut() {
    if (!path_data.use_count() == 1) {
        PathData new_data = *path_data;
        path_data = std::make_shared<PathData>(new_data);
    }
    return *path_data;
}

PathData &BFSPath::get_path_data() /*const*/ {
    return *path_data;
}

bool BFSPath::strong() /*const*/ {
    return confidence == 1.0;
}

void bfs_visit(/*const*/ GI_ref_weak root, std::function<void(BFSPath &)> visitor) {
    PerfCounterAccumulating pc, pc_search, pc_set_insert, pc_setup, pc_deque_insert,
        pc_edges, pc_check_visited, pc_filter, pc_new_path;
    pc_set_insert.pause();
    pc_search.pause();
    pc_deque_insert.pause();
    pc_edges.pause();
    pc_check_visited.pause();
    pc_filter.pause();
    pc_new_path.pause();

    auto node_count = root->get_graph()->node_count();
    std::vector<bool> visited(node_count, false);
    std::vector<bool> visited_weak(node_count, false);
    std::deque<BFSPath> open_path_queue;

    auto handle_path = [&](BFSPath path) {
        pc.pause();
        pc_filter.resume();
        visitor(path);
        pc_filter.pause();
        pc.resume();

        if (path.stop) {
            open_path_queue.clear();
            return;
        }

        if (path.filtered) {
            return;
        }

        pc_set_insert.resume();
        visited_weak[path.last()->v_i] = true;

        if (path.strong()) {
            visited[path.last()->v_i] = true;
        }
        pc_set_insert.pause();

        pc_deque_insert.resume();
        open_path_queue.push_back(std::move(path));
        pc_deque_insert.pause();
    };

    pc_setup.pause();
    handle_path(std::move(BFSPath(root)));

    pc_search.resume();
    while (!open_path_queue.empty()) {
        auto path = std::move(open_path_queue.front());
        open_path_queue.pop_front();

        pc_edges.resume();
        auto edges = path.last()->get_gif_edges();
        pc_edges.pause();
        for (auto &neighbour : edges) {
            pc_check_visited.resume();
            if (visited[neighbour->v_i]) {
                pc_check_visited.pause();
                continue;
            }
            if (visited_weak[neighbour->v_i] && path.contains(neighbour)) {
                pc_check_visited.pause();
                continue;
            }
            pc_check_visited.pause();

            pc_new_path.resume();
            auto new_path = path + neighbour;
            pc_new_path.pause();
            pc_search.pause();
            handle_path(std::move(new_path));
            pc_search.resume();
        }
    }
    pc_set_insert.pause();
    pc_search.pause();
    pc.pause();

    printf("   TIME: %3.2lf ms BFS Check Visited\n", pc_check_visited.ms());
    printf("   TIME: %3.2lf ms BFS Edges\n", pc_edges.ms());
    printf("   TIME: %3.2lf ms BFS New Path\n", pc_new_path.ms());
    printf("  TIME: %3.2lf ms BFS Search\n", pc_search.ms());
    printf("  TIME: %3.2lf ms BFS Setup\n", pc_setup.ms());
    printf("  TIME: %3.2lf ms BFS Set Insert\n", pc_set_insert.ms());
    printf("  TIME: %3.2lf ms BFS Deque Insert\n", pc_deque_insert.ms());
    printf(" TIME: %3.2lf ms BFS Non-filter total\n", pc.ms());
    printf(" TIME: %3.2lf ms BFS Filter total\n", pc_filter.ms());
}
