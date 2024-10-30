/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <graph/graph.hpp>

class GraphInterfaceSelf : public GraphInterface {
  public:
    GraphInterfaceSelf()
      : GraphInterface() {
    }

    static std::shared_ptr<GraphInterfaceSelf> factory() {
        auto gi = std::make_shared<GraphInterfaceSelf>();
        gi->register_graph(gi);
        return gi;
    }
};

class GraphInterfaceHierarchical : public GraphInterface {
    bool is_parent;

  public:
    GraphInterfaceHierarchical(bool is_parent)
      : GraphInterface()
      , is_parent(is_parent) {
    }

    static std::shared_ptr<GraphInterfaceHierarchical> factory(bool is_parent) {
        auto gi = std::make_shared<GraphInterfaceHierarchical>(is_parent);
        gi->register_graph(gi);
        return gi;
    }

    bool get_is_parent() {
        return this->is_parent;
    }
};

class GraphInterfaceReference : public GraphInterface {
  public:
    GraphInterfaceReference()
      : GraphInterface() {
    }

    static std::shared_ptr<GraphInterfaceReference> factory() {
        auto gi = std::make_shared<GraphInterfaceReference>();
        gi->register_graph(gi);
        return gi;
    }
};
