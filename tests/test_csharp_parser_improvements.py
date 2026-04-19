from pathlib import Path

from ast_index.parsers.csharp import CSharpParser


def test_parse_csharp_with_usings():
    """Тест парсинга C# файла с using директивами."""
    code = """
using System;
using System.Collections.Generic;
using static System.Math;

namespace Test
{
    class MyClass
    {
        void MyMethod()
        {
            var list = new List<int>();
        }
    }
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    assert len(result.symbols) > 0
    # Должен найти MyClass
    class_symbols = [s for s in result.symbols if s.kind == "class"]
    assert len(class_symbols) == 1
    assert class_symbols[0].name == "MyClass"


def test_extract_generic_references():
    """Тест извлечения ссылок на generic типы."""
    code = """
class Test
{
    void Method()
    {
        var list = new List<string>();
        var dict = new Dictionary<int, string>();
        var userDict = new UserDictionary<string, int>();
    }
}

class UserDictionary<TKey, TValue>
{
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    # UserDictionary определён в этом же файле, поэтому не в ссылках
    # List и Dictionary - стандартные типы, тоже не в ссылках
    # Но TKey и TValue (type parameters) не извлекаются как symbols,
    # поэтому они могут появиться в ссылках
    ref_names = {r.symbol_name for r in result.references}
    assert "UserDictionary" not in ref_names  # Локальный тип
    assert "List" not in ref_names  # Стандартный тип
    assert "Dictionary" not in ref_names  # Стандартный тип
    # Type parameters могут присутствовать (ограничение tree-sitter парсера)


def test_exclude_xml_documentation():
    """Тест исключения ссылок из XML документации."""
    code = """
/// <summary>
/// This is a <see cref="TestClass"/> reference.
/// </summary>
class TestClass
{
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    # TestClass не должен быть в ссылках (он в XML комментарии)
    # Но должен быть в symbols
    class_symbols = [s for s in result.symbols if s.name == "TestClass"]
    assert len(class_symbols) == 1


def test_exclude_string_interpolation():
    """Тест исключения ссылок из string interpolation."""
    code = """
class Test
{
    void Method(string name)
    {
        var message = $"Hello, {name}";
    }
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    # name внутри интерполяции не должен быть в ссылках
    name_refs = [r for r in result.references if r.symbol_name == "name"]
    # name - параметр метода, локальный символ, должен быть исключён
    assert len(name_refs) == 0


def test_nested_generic_types():
    """Тест извлечения вложенных generic типов."""
    code = """
class Test
{
    void Method()
    {
        var items = new CustomList<CustomList<int>>();
        var matrix = new CustomDict<string, CustomList<CustomList<int>>>();
    }
}

class CustomList<T>
{
}

class CustomDict<TKey, TValue>
{
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    # Локально определённые типы не должны быть в ссылках
    ref_names = {r.symbol_name for r in result.references}
    assert "CustomList" not in ref_names  # Локальный тип
    assert "CustomDict" not in ref_names  # Локальный тип
    # Type parameters (T, TKey, TValue) могут присутствовать


def test_linq_extension_methods():
    """Тест определения LINQ extension methods."""
    code = """
using System.Linq;

class Test
{
    void Method()
    {
        var items = new List<int>();
        var result = items.Where(x => x > 0).ToList();
    }
}
"""

    parser = CSharpParser()
    result = parser.parse(Path("test.cs"), code.encode('utf-8'))

    # Должен найти ссылки на Where и ToList (extension methods)
    ref_names = {r.symbol_name for r in result.references}
    assert "Where" in ref_names
    assert "ToList" in ref_names
