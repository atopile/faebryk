/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "graph.hpp"

class LinkNamedParent;

class GraphInterfaceSelf : public GraphInterface {
  public:
    using GraphInterface::GraphInterface;
};

class GraphInterfaceHierarchical : public GraphInterface {
    bool is_parent;

  public:
    GraphInterfaceHierarchical(bool is_parent);

    template <typename T> static std::shared_ptr<T> factory(bool is_parent);
    bool get_is_parent();
    std::vector<std::pair<Node_ref, std::string>> get_children();
    std::optional<std::pair<Node_ref, std::string>> get_parent();
    void disconnect_parent();

  private:
    std::optional<std::shared_ptr<LinkNamedParent>> get_parent_link();
};

/** Represents a reference to a node object */
class GraphInterfaceReference : public GraphInterface {
  public:
    /** Cannot resolve unbound reference */
    struct UnboundError : public std::runtime_error {
        UnboundError(const std::string &msg)
          : std::runtime_error(msg) {
        }
    };

  public:
    using GraphInterface::GraphInterface;

    GraphInterfaceSelf *get_referenced_gif();
    Node_ref get_reference();
};

// TODO move those back to python when inherited GIFs work again

class GraphInterfaceModuleSibling : public GraphInterfaceHierarchical {
  public:
    using GraphInterfaceHierarchical::GraphInterfaceHierarchical;
};

class GraphInterfaceModuleConnection : public GraphInterface {
  public:
    using GraphInterface::GraphInterface;
};

template <typename T>
inline std::shared_ptr<T> GraphInterfaceHierarchical::factory(bool is_parent) {
    static_assert(std::is_base_of<GraphInterfaceHierarchical, T>::value,
                  "T must be a subclass of GraphInterfaceHierarchical");

    auto gi = std::make_shared<T>(is_parent);
    gi->register_graph(gi);
    return gi;
}