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

class GraphInterfaceReference : public GraphInterface {
  public:
    GraphInterfaceReference();

    static std::shared_ptr<GraphInterfaceReference> factory();
};
