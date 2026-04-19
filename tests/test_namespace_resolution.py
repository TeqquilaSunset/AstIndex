from ast_index.namespace_resolution import extract_using_directives


def test_extract_simple_using():
    code = """using System;
using System.Collections.Generic;
"""
    mapping = extract_using_directives(code, "test.cs")

    assert "System" in mapping.imports
    assert "System.Collections.Generic" in mapping.imports
    assert len(mapping.aliases) == 0
    assert len(mapping.static_imports) == 0


def test_extract_static_using():
    code = """using static System.Math;
"""
    mapping = extract_using_directives(code, "test.cs")

    assert "System.Math" in mapping.static_imports
    assert len(mapping.imports) == 0


def test_extract_alias_using():
    code = """using App = MyNamespace.App;
using Serv = MyNamespace.Services;
"""
    mapping = extract_using_directives(code, "test.cs")

    assert mapping.aliases["App"] == "MyNamespace.App"
    assert mapping.aliases["Serv"] == "MyNamespace.Services"


def test_extract_mixed_using():
    code = """using System;
using static System.Math;
using App = MyNamespace.App;
"""
    mapping = extract_using_directives(code, "test.cs")

    assert "System" in mapping.imports
    assert "System.Math" in mapping.static_imports
    assert mapping.aliases["App"] == "MyNamespace.App"


def test_ignore_comments_and_preprocessor():
    code = """#define DEBUG
#if DEBUG
using System;
#endif
// This is a comment
using System.Collections;
"""
    mapping = extract_using_directives(code, "test.cs")

    assert "System.Collections" in mapping.imports
    assert "System" not in mapping.imports  # Inside #if
