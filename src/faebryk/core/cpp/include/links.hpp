/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "graph/graph.hpp"
#include "graphinterfaces.hpp"

class LinkParent : public Link {
    GraphInterfaceHierarchical *parent;
    GraphInterfaceHierarchical *child;

  public:
    LinkParent(GraphInterfaceHierarchical *from, GraphInterfaceHierarchical *to)
      : Link(from, to) {
        if (from->get_is_parent() && !to->get_is_parent()) {
            this->parent = from;
            this->child = to;
        } else if (!from->get_is_parent() && to->get_is_parent()) {
            this->parent = to;
            this->child = from;
        } else {
            throw std::runtime_error("invalid parent-child relationship");
        }
    }

    GraphInterfaceHierarchical *get_parent() {
        return this->parent;
    }

    GraphInterfaceHierarchical *get_child() {
        return this->child;
    }
};

class LinkNamedParent : public LinkParent {
    std::string name;

  public:
    LinkNamedParent(std::string name, GraphInterfaceHierarchical *from,
                    GraphInterfaceHierarchical *to)
      : LinkParent(from, to)
      , name(name) {
    }

    std::string get_name() {
        return this->name;
    }
};

class LinkDirectShallow : public LinkDirect {
    // TODO
};

/**
 * @brief A Link that points towards a self-gif
 */
class LinkPointer : public Link {
    // TODO
  public:
    LinkPointer(GI_ref_weak from, GI_ref_weak to)
      : Link(from, to) {
    }
};

/**
 * @brief A link represents a connection between a self-gif and a gif in the same node
 */
class LinkSibling : public LinkPointer {
  public:
    LinkSibling(GI_ref_weak from, GI_ref_weak to)
      : LinkPointer(from, to) {
    }
};
