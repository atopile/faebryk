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

    void set_connections(GI_ref_weak from, GI_ref_weak to) override;
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
    GraphInterfaceSelf *pointee;
    GraphInterface *pointer;

  public:
    LinkPointer();
    LinkPointer(GI_ref_weak from, GraphInterfaceSelf *to);
    void set_connections(GI_ref_weak from, GI_ref_weak to) override;
    GraphInterface *get_pointer();
    GraphInterfaceSelf *get_pointee();
};

class LinkSibling : public LinkPointer {
  public:
    LinkSibling();
    LinkSibling(GI_ref_weak from, GraphInterfaceSelf *to);
};

class LinkDirectConditional : public LinkDirect {

  public:
    enum FilterResult {
        FILTER_PASS,
        FILTER_FAIL_RECOVERABLE,
        FILTER_FAIL_UNRECOVERABLE
    };

    using FilterF = std::function<FilterResult(GI_ref_weak from, GI_ref_weak to)>;

    struct LinkFilteredException : public std::runtime_error {
        LinkFilteredException(std::string msg)
          : std::runtime_error(msg) {
        }
    };

  private:
    FilterF filter;
    bool needs_only_first_in_path;

  public:
    LinkDirectConditional(FilterF filter, bool needs_only_first_in_path);
    LinkDirectConditional(FilterF filter, bool needs_only_first_in_path,
                          GI_ref_weak from, GI_ref_weak to);
    void set_connections(GI_ref_weak from, GI_ref_weak to) override;
    FilterResult run_filter(GI_ref_weak from, GI_ref_weak to);

    bool needs_to_check_only_first_in_path();
};

class LinkDirectDerived : public LinkDirectConditional {
  private:
    static LinkDirectConditional::FilterF make_filter_from_path(Path path);

  public:
    LinkDirectDerived(Path path);
    LinkDirectDerived(Path path, GI_ref_weak from, GI_ref_weak to);
};
