"""
Ключевые слова и стандартные типы для разных языков программирования.

Используется для фильтрации ссылок при извлечении использований символов.
"""

# Python
PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield"
}

PYTHON_STANDARD_TYPES = {
    "bool", "int", "float", "str", "list", "dict", "set", "tuple",
    "frozenset", "bytes", "bytearray", "memoryview",
    "range", "enumerate", "reversed", "sorted", "iter",
    "abs", "all", "any", "ascii", "bin", "chr", "dir", "divmod",
    "eval", "exec", "filter", "format", "getattr", "globals",
    "hasattr", "hash", "help", "hex", "id", "input", "isinstance",
    "issubclass", "len", "locals", "map", "max", "min", "next",
    "object", "open", "ord", "pow", "print", "property", "repr",
    "setattr", "slice", "staticmethod", "sum", "super", "type", "vars",
    "zip"
}

# C#
CSHARP_KEYWORDS = {
    "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
    "char", "checked", "class", "const", "continue", "decimal", "default",
    "delegate", "do", "double", "else", "enum", "event", "explicit",
    "extern", "false", "finally", "fixed", "float", "for", "foreach",
    "goto", "if", "implicit", "in", "int", "interface", "internal",
    "is", "lock", "long", "namespace", "new", "null", "object", "operator",
    "out", "override", "params", "private", "protected", "public",
    "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof",
    "static", "string", "struct", "switch", "this", "throw", "true",
    "try", "typeof", "uint", "ulong", "unchecked", "unsafe", "ushort",
    "using", "var", "virtual", "void", "volatile", "when", "where",
    "yield", "async", "await", "nint", "nuint", "record", "with", "init",
    "required", "file", "line", "allow"
}

CSHARP_STANDARD_TYPES = {
    # Примитивные типы и алиасы
    "object", "string", "bool", "byte", "sbyte", "char", "decimal",
    "double", "float", "int", "uint", "long", "ulong", "short", "ushort",
    "nint", "nuint",
    # .NET типы
    "Object", "String", "Boolean", "Byte", "SByte", "Char", "Decimal",
    "Double", "Single", "Int32", "UInt32", "Int64", "UInt64", "Int16",
    "UInt16", "IntPtr", "UIntPtr",
    # Collections
    "Array", "List", "Dictionary", "HashSet", "Queue", "Stack",
    "LinkedList", "SortedList", "SortedDictionary", "SortedSet",
    "ObservableCollection", "Collection",
    # Interfaces
    "IEnumerable", "ICollection", "IList", "IDictionary", "IReadOnlyList",
    "IReadOnlyCollection", "IReadOnlyDictionary", "IQueryable", "IEnumerator",
    "IEqualityComparer", "IComparer",
    # Generics
    "Nullable", "Tuple", "ValueTuple", "Lazy", "Task",
    # LINQ
    "Enumerable", "Queryable", "IGrouping", "ILookup",
    # Common .NET types
    "DateTime", "DateTimeOffset", "TimeSpan", "Guid", "Uri", "Version",
    "StringBuilder", "StringComparison", "StringSplitOptions",
    # Exceptions
    "Exception", "ArgumentException", "ArgumentNullException",
    "ArgumentOutOfRangeException", "InvalidOperationException",
    "NotSupportedException", "NotImplementedException", "IOException",
    "FileNotFoundException", "DirectoryNotFoundException",
    # Attributes
    "Attribute", "ObsoleteAttribute", "SerializableAttribute",
    # Threading
    "Thread", "TaskFactory", "CancellationToken", "CancellationTokenSource",
    "Mutex", "SemaphoreSlim", "Monitor",
    # IO
    "Stream", "FileStream", "MemoryStream", "StreamReader", "StreamWriter",
    "TextReader", "TextWriter", "BinaryReader", "BinaryWriter",
    "File", "Directory", "Path", "FileInfo", "DirectoryInfo",
    # Reflection
    "Type", "TypeInfo", "MemberInfo", "MethodInfo", "PropertyInfo", "FieldInfo",
    "Assembly", "AssemblyName",
    # Text/Encoding
    "Encoding", "UTF8Encoding", "ASCIIEncoding", "CultureInfo", "Regex",
    "Match", "Group", "Capture",
    # Logging
    "ILogger", "ILoggerFactory", "LogLevel",
    # Dependency Injection
    "IServiceProvider", "IServiceCollection", "IServiceScope"
}

# JavaScript
JAVASCRIPT_KEYWORDS = {
    "abstract", "arguments", "await", "boolean", "break", "byte", "case",
    "catch", "char", "class", "const", "continue", "debugger", "default",
    "delete", "do", "double", "else", "enum", "eval", "export", "extends",
    "false", "final", "finally", "float", "for", "function", "goto", "if",
    "implements", "import", "in", "instanceof", "int", "interface", "let",
    "long", "native", "new", "null", "package", "private", "protected",
    "public", "return", "short", "static", "super", "switch", "synchronized",
    "this", "throw", "throws", "transient", "true", "try", "typeof", "var",
    "void", "volatile", "while", "with", "yield"
}

JAVASCRIPT_STANDARD_TYPES = {
    "Object", "Array", "String", "Number", "Boolean", "Date", "RegExp",
    "Error", "TypeError", "SyntaxError", "ReferenceError",
    "Map", "Set", "WeakMap", "WeakSet",
    "Promise", "Proxy", "Reflect", "Symbol",
    "JSON", "Math", "console",
    "ArrayBuffer", "SharedArrayBuffer", "DataView",
    "Int8Array", "Uint8Array", "Uint8ClampedArray",
    "Int16Array", "Uint16Array", "Int32Array", "Uint32Array",
    "Float32Array", "Float64Array",
    "Function", "Arguments"
}

# TypeScript (дополняет JavaScript)
TYPESCRIPT_KEYWORDS = JAVASCRIPT_KEYWORDS | {
    "abstract", "declare", "enum", "interface", "keyof", "module",
    "namespace", "never", "readonly", "type", "unique", "unknown"
}

TYPESCRIPT_STANDARD_TYPES = JAVASCRIPT_STANDARD_TYPES | {
    "Record", "Partial", "Required", "Readonly", "Pick", "Omit",
    "Exclude", "Extract", "ReturnType", "InstanceType",
    "Uppercase", "Lowercase", "Capitalize", "Uncapitalize"
}


def get_keywords(language: str) -> set:
    """Получить ключевые слова для языка."""
    language_lower = language.lower()
    if language_lower == "python":
        return PYTHON_KEYWORDS
    elif language_lower in ("csharp", "c#"):
        return CSHARP_KEYWORDS
    elif language_lower == "javascript":
        return JAVASCRIPT_KEYWORDS
    elif language_lower == "typescript":
        return TYPESCRIPT_KEYWORDS
    else:
        return set()


def get_standard_types(language: str) -> set:
    """Получить стандартные типы для языка."""
    language_lower = language.lower()
    if language_lower == "python":
        return PYTHON_STANDARD_TYPES
    elif language_lower in ("csharp", "c#"):
        return CSHARP_STANDARD_TYPES
    elif language_lower == "javascript":
        return JAVASCRIPT_STANDARD_TYPES
    elif language_lower == "typescript":
        return TYPESCRIPT_STANDARD_TYPES
    else:
        return set()
