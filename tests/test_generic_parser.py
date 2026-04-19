from ast_index.generic_parser import (
    GenericType,
    extract_generic_types,
    get_generic_reference_candidates,
)


def test_extract_simple_generic():
    code = 'var list = new List<string>();'
    generics = extract_generic_types(code, "test.cs", 1)

    assert len(generics) == 1
    assert generics[0].base_type == "List"
    assert generics[0].type_arguments == ["string"]


def test_extract_generic_with_two_args():
    code = 'var dict = new Dictionary<int, string>();'
    generics = extract_generic_types(code, "test.cs", 1)

    assert len(generics) == 1
    assert generics[0].base_type == "Dictionary"
    assert generics[0].type_arguments == ["int", "string"]


def test_extract_nested_generic():
    code = 'var items = new List<List<int>>();'
    generics = extract_generic_types(code, "test.cs", 1)

    assert len(generics) == 1
    assert generics[0].base_type == "List"
    assert len(generics[0].type_arguments) == 1
    assert generics[0].type_arguments[0] == "List<int>"


def test_extract_multiple_generics_in_line():
    code = 'List<int> list = new Dictionary<string, List<int>>();'
    generics = extract_generic_types(code, "test.cs", 1)

    assert len(generics) == 2


def test_get_generic_reference_candidates_simple():
    generic = GenericType(
        base_type="List",
        type_arguments=["string"],
        full_name="List<string>"
    )

    candidates = get_generic_reference_candidates(generic)
    assert "List" in candidates
    assert "string" in candidates


def test_get_generic_reference_candidates_nested():
    generic = GenericType(
        base_type="Dictionary",
        type_arguments=["int", "List<string>"],
        full_name="Dictionary<int, List<string>>"
    )

    candidates = get_generic_reference_candidates(generic)
    assert "Dictionary" in candidates
    assert "int" in candidates
    assert "List" in candidates
    assert "string" in candidates


def test_no_generics_in_code():
    code = 'var x = 42;'
    generics = extract_generic_types(code, "test.cs", 1)

    assert len(generics) == 0


def test_empty_generic():
    code = 'var x = List<>();'
    generics = extract_generic_types(code, "test.cs", 1)
    assert len(generics) == 0  # Empty generics should be skipped


def test_mixed_spaces_around_brackets():
    code = 'var list = new List < string >();'
    generics = extract_generic_types(code, "test.cs", 1)
    assert len(generics) == 1
    assert generics[0].base_type == "List"
    assert generics[0].type_arguments == ["string"]


def test_unbalanced_brackets():
    code = 'var list = new List<int;'
    generics = extract_generic_types(code, "test.cs", 1)
    assert len(generics) == 0  # Should skip malformed generics
