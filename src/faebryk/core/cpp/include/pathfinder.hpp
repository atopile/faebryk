#pragma once

#include "graph.hpp"
#include <any>

inline bool INDIV_MEASURE = true;
inline uint32_t MAX_PATHS = 100000;

struct Edge {
    GraphInterface &from;
    GraphInterface &to;
};

struct PathStackElement {
    NodeGranularType parent_type;
    NodeGranularType child_type;
    GraphInterface &parent_gif;
    std::string name;
    bool up;
};

struct UnresolvedStackElement {
    PathStackElement elem;
    bool promise;

    bool match(PathStackElement &other) {
        return elem.parent_type == other.parent_type &&
               elem.child_type == other.child_type && elem.name == other.name &&
               elem.up != other.up;
    }
};

using PathStack = std::vector<PathStackElement>;
using UnresolvedStack = std::vector<UnresolvedStackElement>;

struct BFSPath {
    std::vector<GraphInterface *> path;
    double confidence = 1.0;
    bool filtered = false;
    bool stop = false;
    // std::unordered_map<std::string, void *> path_data = {};
    // TODO replace with generic path_data
    std::pair<UnresolvedStack, PathStack> path_data;

    bool strong() {
        return confidence == 1.0;
    }
    Link &get_link(Edge edge) {
        auto out = edge.from.is_connected(edge.to);
        assert(out);
        return *out;
    }

    std::optional<Edge> last_edge() {
        if (path.size() < 2) {
            return {};
        }
        return Edge{*path[path.size() - 2], *path[path.size() - 1]};
    }

    BFSPath operator+(GraphInterface &gif) {
        auto new_path = std::vector<GraphInterface *>(path);
        new_path.push_back(&gif);
        return BFSPath{new_path, confidence, filtered, stop, path_data};
    }

    // vector interface
    GraphInterface &last() {
        return *path.back();
    }
    GraphInterface &first() {
        return *path.front();
    }
    GraphInterface &operator[](int idx) {
        return *path[idx];
    }
    size_t size() {
        return path.size();
    }
    bool contains(GraphInterface &gif) {
        return std::find(path.begin(), path.end(), &gif) != path.end();
    }
};

void bfs_visit(GraphInterface &root, std::function<void(BFSPath &)> visitor) {
    std::unordered_set<GraphInterface *> visited;
    std::unordered_set<GraphInterface *> visited_weak;
    std::deque<BFSPath> open_path_queue;

    auto handle_path = [&](BFSPath &path) {
        visitor(path);

        if (path.stop) {
            open_path_queue.clear();
            return;
        }

        if (path.filtered) {
            return;
        }

        visited_weak.insert(&path.last());

        if (path.strong()) {
            visited.insert(&path.last());
        }

        open_path_queue.push_back(path);
    };

    auto root_path = BFSPath{std::vector<GraphInterface *>{&root}};
    handle_path(root_path);

    while (!open_path_queue.empty()) {
        auto path = open_path_queue.front();
        open_path_queue.pop_front();

        auto edges = path.last().edges();
        for (auto &neighbour : edges) {
            if (visited.contains(neighbour)) {
                continue;
            }
            if (path.contains(*neighbour)) {
                continue;
            }

            auto new_path = path + *neighbour;
            handle_path(new_path);
        }
    }
}

class PathFinder;
struct Counter {
    size_t in_cnt = 0;
    size_t weak_in_cnt = 0;
    size_t out_weaker = 0;
    size_t out_stronger = 0;
    size_t out_cnt = 0;
    double time_spent_s = 0;

    bool hide = false;
    const char *name = "";
    bool multi = false;
    bool total_counter = false;

    bool exec(PathFinder *pf, bool (PathFinder::*filter)(BFSPath &), BFSPath &p) {
        if (!INDIV_MEASURE && !total_counter) {
            return (pf->*filter)(p);
        }

        // perf pre
        in_cnt++;
        auto confidence_pre = p.confidence;
        if (confidence_pre < 1.0) {
            weak_in_cnt++;
        }
        auto start = std::chrono::high_resolution_clock::now();

        // exec
        bool res = (pf->*filter)(p);

        // perf post
        auto end = std::chrono::high_resolution_clock::now();
        auto duration =
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
        int64_t duration_ns = duration.count();
        time_spent_s += duration_ns * 1e-9;

        if (res) {
            out_cnt++;
        }
        if (p.confidence < confidence_pre) {
            out_weaker++;
        } else if (p.confidence > confidence_pre) {
            out_stronger++;
        }

        return res;
    }
};

struct Filter {
    bool (PathFinder::*filter)(BFSPath &);
    bool discovery = false;

    Counter counter;

    bool exec(PathFinder *pf, BFSPath &p) {
        bool out = counter.exec(pf, filter, p);
        if (!out && discovery) {
            p.filtered = true;
        }
        return out;
    }
};

class PathFinder {
    Graph &g;

    // instance data
    std::vector<BFSPath> multi_paths;
    size_t path_cnt = 0;

    bool _count(BFSPath &p);
    bool _filter_path_by_node_type(BFSPath &p);
    bool _filter_path_gif_type(BFSPath &p);
    bool _filter_path_by_dead_end_split(BFSPath &p);
    // bool _mark_path_with_promises_heuristic(BFSPath &p);
    bool _build_path_stack(BFSPath &p);
    // bool _filter_path_by_dead_end_split_full(BFSPath &p);
    // bool _build_path_stack_full(BFSPath &p);
    // bool _filter_path_by_dst(BFSPath &p, std::unordered_set<double>
    // &dst_self);
    bool _filter_path_by_end_in_self_gif(BFSPath &p);
    bool _filter_path_same_end_type(BFSPath &p);
    bool _filter_path_by_stack(BFSPath &p);
    bool _filter_and_mark_path_by_link_filter(BFSPath &p);
    std::vector<BFSPath> _filter_paths_by_split_join(std::vector<BFSPath> &paths);

  public:
    PathFinder(Graph &g)
      : g(g) {
    }

    // Create a vector of function pointers to member functions
    std::vector<Filter> filters{
        Filter{
            .filter = &PathFinder::_count,
            .discovery = true,
            .counter =
                Counter{
                    .hide = true,
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_by_node_type,
            .discovery = true,
            .counter =
                Counter{
                    .name = "node type",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_gif_type,
            .discovery = true,
            .counter =
                Counter{
                    .name = "gif type",
                },
        },
        Filter{
            .filter = &PathFinder::_build_path_stack,
            .discovery = false,
            .counter =
                Counter{
                    .name = "build stack",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_by_dead_end_split,
            .discovery = true,
            .counter =
                Counter{
                    .name = "dead end split",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_by_end_in_self_gif,
            .discovery = false,
            .counter =
                Counter{
                    .name = "end in self gif",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_same_end_type,
            .discovery = false,
            .counter =
                Counter{
                    .name = "same end type",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_path_by_stack,
            .discovery = false,
            .counter =
                Counter{
                    .name = "stack",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_and_mark_path_by_link_filter,
            .discovery = true,
            .counter =
                Counter{
                    .name = "link filter",
                },
        },
    };
    bool run_filters(BFSPath &p) {
        for (auto &filter : filters) {
            bool res = filter.exec(this, p);
            if (!res) {
                return false;
            }
        }
        return true;
    }

    std::pair<std::vector<Path>, std::vector<Counter>>
    find_paths(Node &src, std::vector<Node> &dst) {
        if (!src.is_instance(NodeType::N_MODULEINTERFACE)) {
            throw std::runtime_error("src type is not MODULEINTERFACE");
        }
        std::unordered_set<int64_t> dst_py_ids;
        for (auto &d : dst) {
            if (!d.is_instance(NodeType::N_MODULEINTERFACE)) {
                throw std::runtime_error("dst type is not MODULEINTERFACE");
            }
            dst_py_ids.insert(d.self_gif.py_ptr);
        }

        std::vector<BFSPath> paths;

        Counter total_counter{.name = "total", .total_counter = true};

        bfs_visit(src.self_gif, [&](BFSPath &p) {
            bool res = total_counter.exec(this, &PathFinder::run_filters, p);
            if (!res) {
                return;
            }
            // shortcut if path to dst found
            if (dst_py_ids.contains(p.last().py_ptr)) {
                dst_py_ids.erase(p.last().py_ptr);
                if (dst_py_ids.empty()) {
                    p.stop = true;
                }
            }
            paths.push_back(p);
        });

        auto multi_paths = this->_filter_paths_by_split_join(paths);

        std::vector<Path> paths_out;
        for (auto &p : paths) {
            paths_out.push_back(Path(p.path));
        }
        for (auto &p : multi_paths) {
            paths_out.push_back(Path(p.path));
        }

        std::vector<Counter> counters;
        for (auto &f : filters) {
            auto &counter = f.counter;
            if (counter.hide) {
                continue;
            }
            counters.push_back(counter);
        }
        counters.push_back(total_counter);

        return std::make_pair(paths_out, counters);
    }
};

bool PathFinder::_count(BFSPath &p) {
    path_cnt++;
    if (path_cnt % 50000 == 0) {
        std::cout << "path_cnt: " << path_cnt << std::endl;
    }
    // TODO remove
    if (path_cnt > MAX_PATHS) {
        p.stop = true;
    }
    return true;
}

bool PathFinder::_filter_path_by_node_type(BFSPath &p) {
    return (p.last().get_node().is_instance(NodeType::N_MODULEINTERFACE));
}

bool PathFinder::_filter_path_gif_type(BFSPath &p) {
    auto &type = p.last().type;
    return (type == GraphInterfaceType::G_SELF ||
            type == GraphInterfaceType::G_HIERARCHICAL_NODE ||
            type == GraphInterfaceType::G_HIERARCHICAL_MODULE_SPECIAL ||
            type == GraphInterfaceType::G_MODULE_CONNECTION);
}

bool PathFinder::_filter_path_by_end_in_self_gif(BFSPath &p) {
    return p.last().type == GraphInterfaceType::G_SELF;
}

bool PathFinder::_filter_path_same_end_type(BFSPath &p) {
    return p.last().node->granular_type == p.first().node->granular_type;
}

std::optional<PathStackElement> _extend_path_hierarchy_stack(Edge &edge) {
    bool up = edge.from.is_uplink(edge.to);
    if (!up && !edge.from.is_downlink(edge.to)) {
        return {};
    }
    auto child_gif = up ? edge.from : edge.to;
    auto parent_gif = up ? edge.to : edge.from;

    assert(child_gif.parent_name);
    auto name = *child_gif.parent_name;
    return PathStackElement{parent_gif.get_node().granular_type,
                            child_gif.get_node().granular_type, parent_gif, name, up};
}

void _extend_fold_stack(PathStackElement &elem, UnresolvedStack &unresolved_stack,
                        PathStack &promise_stack) {
    if (!unresolved_stack.empty() && unresolved_stack.back().match(elem)) {
        auto promise = unresolved_stack.back().promise;
        if (promise) {
            promise_stack.push_back(elem);
        }
    } else {
        // TODO get children and count instead
        bool multi_child = true;
        // if down and multipath -> promise
        bool promise = !elem.up and multi_child;

        unresolved_stack.push_back(UnresolvedStackElement{elem, promise});
        if (promise) {
            promise_stack.push_back(elem);
        }
    }
}

bool PathFinder::_build_path_stack(BFSPath &p) {
    auto edge = p.last_edge();
    if (!edge) {
        return true;
    }

    auto elem = _extend_path_hierarchy_stack(*edge);
    if (!elem) {
        return true;
    }

    auto &promises = p.path_data;
    auto &unresolved_stack_ = promises.first;
    auto &promise_stack_ = promises.second;

    std::vector<UnresolvedStackElement> unresolved_stack(unresolved_stack_);
    std::vector<PathStackElement> promise_stack(promise_stack_);

    size_t promise_cnt = promise_stack.size();
    _extend_fold_stack(elem.value(), unresolved_stack, promise_stack);

    p.path_data = std::make_pair(unresolved_stack, promise_stack);

    int promise_growth = promise_stack.size() - promise_cnt;
    p.confidence *= std::pow(0.5, promise_growth);

    return true;
}

bool PathFinder::_filter_path_by_stack(BFSPath &p) {

    auto promises = p.path_data;
    auto &unresolved_stack = promises.first;
    auto &promise_stack = promises.second;

    if (!unresolved_stack.empty()) {
        return false;
    }

    if (!promise_stack.empty()) {
        this->multi_paths.push_back(p);
        return false;
    }

    return true;
}

bool PathFinder::_filter_path_by_dead_end_split(BFSPath &p) {
    if (p.path.size() < 3) {
        return true;
    }
    for (auto it = p.path.end() - 3; it != p.path.end(); ++it) {
        GraphInterface *gif = *it;
        if (!gif->is_hierarchical()) {
            return true;
        }
    }

    auto &one = p.path[p.path.size() - 3];
    auto &two = p.path[p.path.size() - 2];
    auto &three = p.path[p.path.size() - 1];

    // check if child->parent->child
    if (!one->is_parent && two->is_parent && !three->is_parent) {
        return false;
    }

    return true;
}

// TODO needs link filter exec
bool PathFinder::_filter_and_mark_path_by_link_filter(BFSPath &p) {
    for (size_t i = 0; i < p.path.size() - 1; ++i) {
        Edge edge{*p.path[i], *p.path[i + 1]};

        auto linkobj = p.get_link(edge);

        // TODO remove
        if (linkobj.type == LinkType::L_DIRECT_CONDITIONAL) {
            return false;
        }

        //    auto *conditional_link = dynamic_cast<LinkDirectConditional
        //    *>(linkobj); if (!conditional_link) {
        //        continue;
        //    }

        //    auto result = conditional_link->is_filtered(p.path);
        //    if (result ==
        //    LinkDirectConditional::FilterResult::FAIL_UNRECOVERABLE)
        //    {
        //        return false;
        //    } else if (result ==
        //               LinkDirectConditional::FilterResult::FAIL_RECOVERABLE)
        //               {
        //        p.confidence *= 0.8;
        //    }
    }

    return true;
}

// TODO needs get children
std::vector<BFSPath>
PathFinder::_filter_paths_by_split_join(std::vector<BFSPath> &paths) {
    // std::unordered_set<GraphInterface *> filtered;
    // std::unordered_map<GraphInterface *, std::vector<BFSPath>> split;

    //// build split map
    // for (auto &p : paths) {
    //     auto &promises = p.path_data;
    //     auto &unresolved_stack = promises.first;
    //     auto &promise_stack = promises.second;

    //    if (!unresolved_stack.empty() or promise_stack.empty()) {
    //        continue;
    //    }

    //    for (auto &elem : promise_stack) {
    //        if (elem.up) {
    //            // join
    //            continue;
    //        }
    //        // split
    //        split[&elem.parent_gif].push_back(p);
    //    }
    //}

    //// check split map
    // for (auto &[gif, paths] : split) {
    //     //TODO
    //     std::vector<GraphInterface *> children = gif->get_children();
    //     // ...
    // }

    std::vector<BFSPath> paths_out;
    return paths_out;
}
