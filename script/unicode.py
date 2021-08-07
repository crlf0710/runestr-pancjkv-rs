#!/usr/bin/env python
#
# Copyright 2011-2015 The Rust Project Developers. See the COPYRIGHT
# file at the top-level directory of this distribution and at
# http://rust-lang.org/COPYRIGHT.
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

# This script uses the following Unicode tables:
# - PropertyValueAliases.txt
# - ScriptExtensions.txt
# - Scripts.txt
#
# Since this should not require frequent updates, we just store this
# out-of-line and check the unicode.rs file into git.

import fileinput, re, os, sys

preamble = '''// Copyright 2012-2018 The Rust Project Developers. See the COPYRIGHT
// file at the top-level directory of this distribution and at
// http://rust-lang.org/COPYRIGHT.
//
// Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
// http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
// <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
// option. This file may not be copied, modified, or distributed
// except according to those terms.

// NOTE: The following code was generated by "scripts/unicode.py", do not edit directly

#![allow(missing_docs, non_upper_case_globals, non_snake_case)]

pub use tables_impl::*;

#[rustfmt::skip]
mod tables_impl {
'''

# Close `mod impl {`
ending='''
}
'''

UNICODE_VERSION = (13, 0, 0)

UNICODE_VERSION_NUMBER = "%s.%s.%s" %UNICODE_VERSION

def escape_char(c):
    return "'\\u{%x}'" % c

def fetch(f):
    if not os.path.exists(os.path.basename(f)):
        os.system("curl -O http://www.unicode.org/Public/%s/ucd/%s"
                      % (UNICODE_VERSION_NUMBER, f))

    if not os.path.exists(os.path.basename(f)):
        sys.stderr.write("cannot load %s" % f)
        exit(1)

def format_table_content(f, content, indent):
    line = " "*indent
    first = True
    for chunk in content.split(","):
        if len(line) + len(chunk) < 98:
            if first:
                line += chunk
            else:
                line += ", " + chunk
            first = False
        else:
            f.write(line + ",\n")
            line = " "*indent + chunk
    f.write(line)

# Implementation from unicode-segmentation
def load_properties(f, interesting_script, interesting_gc):
    fetch(f)
    props = {}
    # Note: these regexes are different from those in unicode-segmentation,
    # becase we need to handle spaces here
    re1 = re.compile(r"^ *([0-9A-F]+) *; *([^#]+) *# *([A-Za-z]+) *")
    re2 = re.compile(r"^ *([0-9A-F]+)\.\.([0-9A-F]+) *; *([^#]+) *# *([A-Za-z]+) *")

    for line in fileinput.input(os.path.basename(f), openhook=fileinput.hook_encoded("utf-8")):
        script = None
        gc = None
        d_lo = 0
        d_hi = 0
        m = re1.match(line)
        if m:
            d_lo = m.group(1)
            d_hi = m.group(1)
            script = m.group(2).strip()
            gc = m.group(3)
        else:
            m = re2.match(line)
            if m:
                d_lo = m.group(1)
                d_hi = m.group(2)
                script = m.group(3).strip()
                gc = m.group(4).strip()
            else:
                continue
        if interesting_script and script not in interesting_script:
            continue
        if interesting_gc and gc not in interesting_gc:
            continue
        d_lo = int(d_lo, 16)
        d_hi = int(d_hi, 16)
        if script not in props:
            props[script] = []
        props[script].append((d_lo, d_hi))

    return props

# Implementation from unicode-segmentation
def emit_table(f, name, t_data, t_type = "&'static [(char, char)]", is_pub=True,
        pfun=lambda x: "(%s,%s)" % (escape_char(x[0]), escape_char(x[1])), is_const=True):
    pub_string = "const"
    if not is_const:
        pub_string = "let"
    if is_pub:
        pub_string = "pub " + pub_string
    f.write("    %s %s: %s = &[\n" % (pub_string, name, t_type))
    data = ""
    first = True
    for dat in t_data:
        if not first:
            data += ","
        first = False
        data += pfun(dat)
    format_table_content(f, data, 8)
    f.write("\n    ];\n\n")

def emit_search(f):
    f.write("""
    pub fn bsearch_range_table(c: char, r: &'static [(char, char)]) -> bool {
        use core::cmp::Ordering::{Equal, Less, Greater};
        r.binary_search_by(|&(lo, hi)| {
            if lo <= c && c <= hi { Equal }
            else if hi < c { Less }
            else { Greater }
        }).is_ok()
    }

    #[inline]
    pub fn is_han_script_lo_character(c: char) -> bool {
        bsearch_range_table(c, PAN_CJKV_SCRIPT_LO_RANGE)
    }
""")


if __name__ == "__main__":
    r = "tables.rs"
    if os.path.exists(r):
        os.remove(r)
    with open(r, "w") as rf:
        # write the file's preamble
        rf.write(preamble)
        rf.write("""
/// The version of [Unicode](http://www.unicode.org/)
/// that this version of unicode-script is based on.
pub const UNICODE_VERSION: (u64, u64, u64) = (%s, %s, %s);
""" % UNICODE_VERSION)

        script = 'Han'
        gc = 'Lo'
        scripts = load_properties("Scripts.txt", [script], [gc])
        script_table = []

        script_table.extend([(x, y) for (x, y) in scripts[script]])
        script_table.sort(key=lambda w: w[0])

        emit_search(rf)

        emit_table(rf, "PAN_CJKV_SCRIPT_LO_RANGE", script_table, t_type = "&'static [(char, char)]",
                   is_pub=False , pfun=lambda x: "(%s,%s)" % (escape_char(x[0]), escape_char(x[1])))

        rf.write(ending)