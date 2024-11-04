/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "graph.hpp"

class LinkNamedParent;

class GraphInterfaceSelf : public GraphInterface {
  public:
    GraphInterfaceSelf();

    static std::shared_ptr<GraphInterfaceSelf> factory();
};

class GraphInterfaceHierarchical : public GraphInterface {
    bool is_parent;

  public:
    GraphInterfaceHierarchical(bool is_parent);

    static std::shared_ptr<GraphInterfaceHierarchical> factory(bool is_parent);
    bool get_is_parent();
    std::vector<std::pair<Node_ref, std::string>> get_children();
    std::optional<std::pair<Node_ref, std::string>> get_parent();
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
    GraphInterfaceReference();

    static std::shared_ptr<GraphInterfaceReference> factory();

    GraphInterfaceSelf *get_referenced_gif();
    Node_ref get_reference();
};
