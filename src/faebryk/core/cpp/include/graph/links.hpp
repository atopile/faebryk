/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include "graph/graph.hpp"
#include "graphinterfaces.hpp"

class LinkDirect : public Link {
  public:
    LinkDirect();
    LinkDirect(GI_ref_weak from, GI_ref_weak to);
};

class LinkParent : public Link {
    GraphInterfaceHierarchical *parent;
    GraphInterfaceHierarchical *child;

  public:
    LinkParent();
    LinkParent(GraphInterfaceHierarchical *from, GraphInterfaceHierarchical *to);

    void set_connections(GraphInterfaceHierarchical *from,
                         GraphInterfaceHierarchical *to);
    GraphInterfaceHierarchical *get_parent();
    GraphInterfaceHierarchical *get_child();
};

class LinkNamedParent : public LinkParent {
    std::string name;

  public:
    LinkNamedParent(std::string name);
    LinkNamedParent(std::string name, GraphInterfaceHierarchical *from,
                    GraphInterfaceHierarchical *to);

    std::string get_name();
};

class LinkDirectShallow : public LinkDirect {
    // TODO
};

class LinkPointer : public Link {
    // TODO
  public:
    LinkPointer();
    LinkPointer(GI_ref_weak from, GI_ref_weak to);
};

class LinkSibling : public LinkPointer {
  public:
    LinkSibling();
    LinkSibling(GI_ref_weak from, GI_ref_weak to);
};