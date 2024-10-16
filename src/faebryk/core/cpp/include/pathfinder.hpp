#pragma once

#include "graph.hpp"

struct Edge {
    GraphInterface &from;
    GraphInterface &to;
};

struct BFSPath {
    std::vector<GraphInterface *> path;
    double confidence = 1.0;
    bool filtered = false;
    std::unordered_map<std::string, void *> path_data = {};

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
        return BFSPath{new_path, confidence, filtered, path_data};
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
        std::cout << "edges: " << edges.size() << std::endl;
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

class PathFinder {
    Graph &g;

    std::vector<Path> multi_paths;

    bool _count(BFSPath &p);
    bool _filter_path_by_node_type(BFSPath &p);
    bool _filter_path_gif_type(BFSPath &p);
    bool _filter_path_by_dead_end_split(BFSPath &p);
    // bool _mark_path_with_promises_heuristic(BFSPath &p);
    bool _build_path_stack(BFSPath &p);
    // bool _filter_path_by_dead_end_split_full(BFSPath &p);
    // bool _build_path_stack_full(BFSPath &p);
    bool _filter_path_by_dst(BFSPath &p, std::unordered_set<double> &dst_self);
    bool _filter_path_by_end_in_self_gif(BFSPath &p);
    bool _filter_path_same_end_type(BFSPath &p);
    bool _filter_path_by_stack(BFSPath &p);
    bool _filter_and_mark_path_by_link_filter(BFSPath &p);
    std::vector<BFSPath>
    _filter_paths_by_split_join(std::vector<BFSPath> &paths);

  public:
    PathFinder(Graph &g)
      : g(g) {
    }

    std::vector<Path> find_paths(Node &src, std::vector<Node> &dst) {
        std::cout << "find_paths" << std::endl;
        std::cout << "edge count: " << g.e.size() << std::endl;
        std::cout << "v count: " << g.v.size() << std::endl;

        // throw error if src or dst type is not MODULEINTERFACE
        if (!src.is_instance(NodeType::N_MODULEINTERFACE)) {
            throw std::runtime_error("src type is not MODULEINTERFACE");
        }
        for (auto &d : dst) {
            if (!d.is_instance(NodeType::N_MODULEINTERFACE)) {
                throw std::runtime_error("dst type is not MODULEINTERFACE");
            }
        }

        // Create a vector of function pointers to member functions
        std::vector<std::pair<bool (PathFinder::*)(BFSPath &), bool>> filters{
            {&PathFinder::_filter_path_by_node_type, true},
            //{&PathFinder::_filter_path_gif_type, true},
            //{&PathFinder::_filter_path_by_dead_end_split, true},
            //{&PathFinder::_filter_path_by_end_in_self_gif, true},
            //{&PathFinder::_filter_path_same_end_type, true},
            //{&PathFinder::_filter_path_by_stack, true},
            //{&PathFinder::_filter_and_mark_path_by_link_filter, true},
        };

        std::vector<BFSPath> paths;

        bfs_visit(src.self_gif, [&](BFSPath &p) {
            std::cout << "path: " << p.path.size() << std::endl;

            for (auto &filter : filters) {
                bool discovery = filter.second;
                auto filter_func = filter.first;

                bool res = (this->*filter_func)(p);
                if (discovery && !res) {
                    p.filtered = true;
                }
                if (!res) {
                    return;
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

        return paths_out;
    }
};

bool PathFinder::_filter_path_by_node_type(BFSPath &p) {
    return (p.last().get_node().is_instance(NodeType::N_MODULEINTERFACE));
}

std::vector<BFSPath>
PathFinder::_filter_paths_by_split_join(std::vector<BFSPath> &paths) {
    std::vector<BFSPath> paths_out;

    return paths_out;
}
