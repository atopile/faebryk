#pragma once

#include "graph.hpp"
#include <any>

inline bool INDIV_MEASURE = true;
inline uint32_t MAX_PATHS = 1 << 31;

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

    std::string str() const {
        std::stringstream ss;
        if (up) {
            ss << child_type << "->" << parent_type << "." << name;
        } else {
            ss << parent_type << "." << name << "->" << child_type;
        }
        return ss.str();
    }
};

struct UnresolvedStackElement {
    PathStackElement elem;
    bool promise;

    bool match(PathStackElement &other) {
        return elem.parent_type == other.parent_type &&
               elem.child_type == other.child_type && elem.name == other.name &&
               elem.up != other.up;
    }

    std::string str() const {
        std::stringstream ss;
        ss << elem.str();
        if (promise) {
            ss << " promise";
        }
        return ss.str();
    }
};

using PathStack = std::vector<PathStackElement>;
using UnresolvedStack = std::vector<UnresolvedStackElement>;

struct PathData {
    UnresolvedStack unresolved_stack;
    PathStack promise_stack;
};

class BFSPath {
    std::vector<GraphInterface *> path;
    std::shared_ptr<PathData> path_data;

  public:
    double confidence = 1.0;
    bool filtered = false;
    bool stop = false;

    BFSPath(GraphInterface &path_head)
      : path(std::vector<GraphInterface *>{&path_head})
      , path_data(std::make_shared<PathData>()) {
    }

    BFSPath(const BFSPath &other, GraphInterface &new_head)
      : path(other.path)
      , path_data(other.path_data)
      , confidence(other.confidence)
      , filtered(other.filtered)
      , stop(other.stop) {
        path.push_back(&new_head);
    }

    PathData &get_path_data_mut() {
        if (!path_data.unique()) {
            PathData new_data = *path_data;
            path_data = std::make_shared<PathData>(new_data);
        }
        return *path_data;
    }

    PathData &get_path_data() const {
        return *path_data;
    }

    bool strong() const {
        return confidence == 1.0;
    }
    const Link &get_link(Edge edge) const {
        auto out = edge.from.is_connected(edge.to);
        assert(out);
        const Link &link = **out;
        return link;
    }

    std::optional<Edge> last_edge() const {
        if (path.size() < 2) {
            return {};
        }
        return Edge{*path[path.size() - 2], *path.back()};
    }

    std::optional<std::tuple<GraphInterface *, GraphInterface *, GraphInterface *>>
    last_tri_edge() const {
        if (path.size() < 3) {
            return {};
        }
        return std::make_tuple(path[path.size() - 3], path[path.size() - 2],
                               path.back());
    }

    BFSPath operator+(GraphInterface &gif) {
        return BFSPath(*this, gif);
    }

    // vector interface
    GraphInterface &last() const {
        return *path.back();
    }
    GraphInterface &first() const {
        return *path.front();
    }
    GraphInterface &operator[](int idx) const {
        return *path[idx];
    }

    size_t size() const {
        return path.size();
    }
    bool contains(const GraphInterface &gif) const {
        return std::find(path.begin(), path.end(), &gif) != path.end();
    }

    void iterate_edges(std::function<bool(Edge &)> visitor) const {
        for (size_t i = 1; i < path.size(); i++) {
            Edge edge{*path[i - 1], *path[i]};
            bool res = visitor(edge);
            if (!res) {
                return;
            }
        }
    }

    std::vector<GraphInterface *> &get_path() {
        return path;
    }
};

class PerfCounter {
    std::chrono::high_resolution_clock::time_point start;

  public:
    PerfCounter() {
        start = std::chrono::high_resolution_clock::now();
    }

    int64_t ns() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration =
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
        return duration.count();
    }

    double ms() {
        return ns() / 1e6;
    }

    double s() {
        return ns() / 1e9;
    }
};

class PerfCounterAccumulating {
    std::chrono::high_resolution_clock::time_point start;
    int64_t time_ns = 0;
    bool paused = false;

  public:
    PerfCounterAccumulating() {
        start = std::chrono::high_resolution_clock::now();
    }

    void pause() {
        if (paused) {
            return;
        }
        auto end = std::chrono::high_resolution_clock::now();
        auto duration =
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
        this->time_ns += duration.count();
        paused = true;
    }

    void resume() {
        if (!paused) {
            return;
        }
        start = std::chrono::high_resolution_clock::now();
        paused = false;
    }

    int64_t ns() {
        pause();
        return this->time_ns;
    }

    double ms() {
        return ns() / 1e6;
    }

    double s() {
        return ns() / 1e9;
    }
};

void bfs_visit(GraphInterface &root, std::function<void(BFSPath &)> visitor) {
    PerfCounterAccumulating pc, pc_search, pc_set_insert, pc_setup, pc_deque_insert,
        pc_edges, pc_check_visited, pc_filter, pc_new_path;
    pc_set_insert.pause();
    pc_search.pause();
    pc_deque_insert.pause();
    pc_edges.pause();
    pc_check_visited.pause();
    pc_filter.pause();
    pc_new_path.pause();

    std::vector<bool> visited(root.graph.v.size(), false);
    std::vector<bool> visited_weak(root.graph.v.size(), false);
    std::deque<BFSPath> open_path_queue;

    auto handle_path = [&](BFSPath &path) {
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
        visited_weak[path.last().v_i] = true;

        if (path.strong()) {
            visited[path.last().v_i] = true;
        }
        pc_set_insert.pause();

        pc_deque_insert.resume();
        open_path_queue.push_back(std::move(path));
        pc_deque_insert.pause();
    };

    pc_setup.pause();
    auto root_path = BFSPath(root);
    handle_path(root_path);

    pc_search.resume();
    while (!open_path_queue.empty()) {
        auto path = std::move(open_path_queue.front());
        open_path_queue.pop_front();

        pc_edges.resume();
        auto edges = path.last().edges();
        pc_edges.pause();
        for (auto &neighbour : edges) {
            pc_check_visited.resume();
            if (visited[neighbour->v_i]) {
                pc_check_visited.pause();
                continue;
            }
            if (visited_weak[neighbour->v_i] && path.contains(*neighbour)) {
                pc_check_visited.pause();
                continue;
            }
            pc_check_visited.pause();

            pc_new_path.resume();
            auto new_path = path + *neighbour;
            pc_new_path.pause();
            pc_search.pause();
            handle_path(new_path);
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
        PerfCounter pc;

        // exec
        bool res = (pf->*filter)(p);

        // perf post
        int64_t duration_ns = pc.ns();
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
    bool _filter_shallow(BFSPath &p);
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
            .filter = &PathFinder::_filter_path_by_dead_end_split,
            .discovery = true,
            .counter =
                Counter{
                    .name = "dead end split",
                },
        },
        Filter{
            .filter = &PathFinder::_filter_shallow,
            .discovery = true,
            .counter =
                Counter{
                    .name = "shallow",
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

        PerfCounter pc_bfs;

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

        printf("TIME: %3.2lf ms BFS\n", pc_bfs.ms());

        auto multi_paths = this->_filter_paths_by_split_join(paths);

        std::vector<Path> paths_out;
        for (auto &p : paths) {
            paths_out.push_back(Path(p.get_path()));
        }
        for (auto &p : multi_paths) {
            paths_out.push_back(Path(p.get_path()));
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
    // if (p.path.size() > MAX_PATHS) {
    //     p.stop = true;
    // }
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
        unresolved_stack.pop_back();
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

    auto &promises = p.get_path_data_mut();
    auto &unresolved_stack = promises.unresolved_stack;
    auto &promise_stack = promises.promise_stack;

    size_t promise_cnt = promise_stack.size();
    _extend_fold_stack(elem.value(), unresolved_stack, promise_stack);

    int promise_growth = promise_stack.size() - promise_cnt;
    p.confidence *= std::pow(0.5, promise_growth);

    return true;
}

bool PathFinder::_filter_path_by_stack(BFSPath &p) {
    const auto promises = p.get_path_data();
    auto &unresolved_stack = promises.unresolved_stack;
    auto &promise_stack = promises.promise_stack;

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
    auto last_tri_edge = p.last_tri_edge();
    if (!last_tri_edge) {
        return true;
    }
    auto &[one, two, three] = *last_tri_edge;

    if (!one->is_hierarchical() || !two->is_hierarchical() ||
        !three->is_hierarchical()) {
        return true;
    }

    // check if child->parent->child
    if (!one->is_parent && two->is_parent && !three->is_parent) {
        return false;
    }

    return true;
}

bool PathFinder::_filter_shallow(BFSPath &p) {
    bool ok = true;
    auto edge = p.last_edge();
    if (!edge) {
        return true;
    }
    const auto &linkobj = p.get_link(*edge);

    if (linkobj.type != LinkType::L_DIRECT_CONDITIONAL_SHALLOW) {
        return true;
    }

    return !linkobj.is_filtered(p.first().get_node());
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
