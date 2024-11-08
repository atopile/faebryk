/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#include "pathfinder/pathfinder.hpp"
#include "graph/links.hpp"
#include "pathfinder/bfs.hpp"
#include "pathfinder/pathcounter.hpp"
#include <unordered_map>
#include <unordered_set>

// PathFinder implementations
PathFinder::PathFinder(Graph &g)
  : g(g) {
    filters = {
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
            .filter = &PathFinder::_filter_conditional_link,
            .discovery = true,
            .counter =
                Counter{
                    .name = "conditional link",
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
}

// Filter implementations
bool Filter::exec(PathFinder *pf, BFSPath &p) {
    bool out = counter.exec(pf, filter, p);
    if (!out && discovery) {
        p.filtered = true;
    }
    return out;
}

bool PathFinder::run_filters(BFSPath &p) {
    for (auto &filter : filters) {
        bool res = filter.exec(this, p);
        if (!res) {
            return false;
        }
    }
    return true;
}

std::pair<std::vector<Path>, std::vector<Counter>>
PathFinder::find_paths(Node_ref src, std::vector<Node_ref> dst) {
    if (!src->get_type().is_moduleinterface()) {
        throw std::runtime_error("src type is not MODULEINTERFACE");
    }
    std::unordered_set<Node_ref> dsts;
    for (auto &d : dst) {
        if (!d->get_type().is_moduleinterface()) {
            throw std::runtime_error("dst type is not MODULEINTERFACE");
        }
        dsts.insert(d);
    }

    std::vector<BFSPath> paths;

    Counter total_counter{.name = "total", .total_counter = true};

    PerfCounter pc_bfs;

    bfs_visit(src->get_self_gif().get(), [&](BFSPath p) {
        bool res = total_counter.exec(this, &PathFinder::run_filters, p);
        if (!res) {
            return;
        }
        // shortcut if path to dst found
        auto last = p.last()->get_node();
        if (dsts.contains(last)) {
            dsts.erase(last);
            if (dsts.empty()) {
                p.stop = true;
            }
        }
        paths.push_back(std::move(p));
    });

    printf("TIME: %3.2lf ms BFS\n", pc_bfs.ms());

    Counter counter_split_join{
        .name = "split join",
        .multi = true,
    };
    auto multi_paths = counter_split_join.exec_multi(
        this, &PathFinder::_filter_paths_by_split_join, this->multi_paths);

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
    counters.push_back(counter_split_join);
    counters.push_back(total_counter);

    return std::make_pair(paths_out, counters);
}

bool PathFinder::_count(BFSPath &p) {
    path_cnt++;
    if (path_cnt % 50000 == 0) {
        printf("path_cnt: %lld\n", path_cnt);
    }
    if (path_cnt > MAX_PATHS) {
        p.stop = true;
    }
    return true;
}

bool PathFinder::_filter_path_by_node_type(BFSPath &p) {
    return (p.last()->get_node()->get_type().is_moduleinterface());
}

bool PathFinder::_filter_path_gif_type(BFSPath &p) {
    auto last = p.last();
    return (dynamic_cast<GraphInterfaceSelf *>(last) ||
            dynamic_cast<GraphInterfaceHierarchical *>(last) ||
            dynamic_cast<GraphInterfaceModuleConnection *>(last));
}

bool PathFinder::_filter_path_by_end_in_self_gif(BFSPath &p) {
    return dynamic_cast<GraphInterfaceSelf *>(p.last());
}

bool PathFinder::_filter_path_same_end_type(BFSPath &p) {
    return p.last()->get_node()->get_type() == p.first()->get_node()->get_type();
}

std::optional<PathStackElement> _extend_path_hierarchy_stack(Edge &edge) {
    bool up = GraphInterfaceHierarchical::is_uplink(edge.from, edge.to);
    if (!up && !GraphInterfaceHierarchical::is_downlink(edge.from, edge.to)) {
        return {};
    }
    auto child_gif =
        dynamic_cast<GraphInterfaceHierarchical *>(up ? edge.from : edge.to);
    auto parent_gif =
        dynamic_cast<GraphInterfaceHierarchical *>(up ? edge.to : edge.from);

    auto name = child_gif->get_parent()->second;
    return PathStackElement{parent_gif->get_node()->get_type(),
                            child_gif->get_node()->get_type(), parent_gif, name, up};
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

    auto one_h = dynamic_cast<GraphInterfaceHierarchical *>(one);
    auto two_h = dynamic_cast<GraphInterfaceHierarchical *>(two);
    auto three_h = dynamic_cast<GraphInterfaceHierarchical *>(three);
    if (!one_h || !two_h || !three_h) {
        return true;
    }

    // check if child->parent->child
    if (!one_h->get_is_parent() && two_h->get_is_parent() && !three_h->get_is_parent()) {
        return false;
    }

    return true;
}

bool PathFinder::_filter_conditional_link(BFSPath &p) {
    auto edge = p.last_edge();
    if (!edge) {
        return true;
    }
    /*const*/ auto linkobj = p.get_link(*edge);

    auto link_conditional = dynamic_cast<LinkDirectConditional *>(linkobj);
    if (!link_conditional) {
        return true;
    }

    if (link_conditional->needs_to_check_only_first_in_path()) {
        if (p.size() > 1) {
            return true;
        }
    }

    // TODO check recoverable?
    return link_conditional->run_filter(edge->from, edge->to) ==
           LinkDirectConditional::FilterResult::FILTER_PASS;
}

template <typename T, typename U>
std::unordered_map<U, std::vector<T>> groupby(const std::vector<T> &vec,
                                              std::function<U(T)> f) {
    std::unordered_map<U, std::vector<T>> out;
    for (auto &t : vec) {
        out[f(t)].push_back(t);
    }
    return out;
}

std::vector<BFSPath>
PathFinder::_filter_paths_by_split_join(std::vector<BFSPath> &paths) {
    std::unordered_set</*const*/ BFSPath *> filtered;
    std::unordered_map</*const*/ GI_ref_weak, std::vector</*const*/ BFSPath *>> split;

    // build split map
    for (auto &p : paths) {
        auto &promises = p.get_path_data();
        auto &unresolved_stack = promises.unresolved_stack;
        auto &promise_stack = promises.promise_stack;

        assert(unresolved_stack.empty());
        assert(!promise_stack.empty());

        for (auto &elem : promise_stack) {
            if (elem.up) {
                // join
                continue;
            }
            // split
            split[elem.parent_gif].push_back(&p);
        }
    }

    // check split map
    for (auto &[start_gif, split_paths] : split) {
        auto children = start_gif->get_node()->get_children(
            true, {{Node::Type::get_moduleinterface_type()}}, true);
        auto children_set =
            std::unordered_set<Node_ref>(children.begin(), children.end());

        assert(split_paths.size());
        auto index = split_paths[0]->index(start_gif);

        std::function</*const*/ GI_ref_weak(/*const*/ BFSPath *)> f =
            [index](/*const*/ BFSPath *p) -> /*const*/ GI_ref_weak {
            return p->last();
        };
        auto grouped_by_end = groupby(split_paths, f);

        for (auto &[end_gif, grouped_paths] : grouped_by_end) {
            std::unordered_set<Node_ref> covered_children;
            for (auto &p : grouped_paths) {
                covered_children.insert((*p)[index + 1]->get_node());
            }

            if (covered_children != children_set) {
                filtered.insert(grouped_paths.begin(), grouped_paths.end());
                continue;
            }
        }
    }

    std::vector<BFSPath> paths_out;
    for (BFSPath &p : paths) {
        if (filtered.contains(&p)) {
            continue;
        }
        p.confidence = 1.0;
        paths_out.push_back(p);
    }
    return paths_out;
}
