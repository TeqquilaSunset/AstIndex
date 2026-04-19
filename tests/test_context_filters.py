from ast_index.context_filters import filter_extension_methods, should_exclude_context


def test_exclude_xml_documentation():
    line = '/// <summary>This is a summary</summary>'
    assert should_exclude_context(line, 3, "summary")


def test_exclude_inside_attribute():
    line = '[Obsolete("Do not use")]'
    # Проверим позицию внутри Obsolete
    col_start = line.find('Obsolete')
    assert should_exclude_context(line, col_start, "Obsolete")


def test_not_exclude_normal_code():
    line = 'var user = new User();'
    col_start = line.find('User')
    assert not should_exclude_context(line, col_start, "User")


def test_exclude_string_interpolation():
    line = 'var message = $"User: {user.Name}";'
    # user.Name внутри интерполяции
    user_col = line.find('user')
    name_col = line.find('Name')
    assert should_exclude_context(line, user_col, "user")
    assert should_exclude_context(line, name_col, "Name")


def test_filter_linq_extension_methods():
    line = 'users.Where(u => u.Id > 0).ToList()'

    # Where - extension method
    line.find('Where')
    assert filter_extension_methods("Where", line, set())

    # ToList - extension method
    line.find('ToList')
    assert filter_extension_methods("ToList", line, set())

    # Id - не extension method
    line.find('Id')
    assert not filter_extension_methods("Id", line, set())


def test_filter_custom_extension_methods():
    line = 'items.MyCustomExtension()'

    # Если MyCustomExtension в known_extensions
    known_extensions = {'MyCustomExtension'}
    line.find('MyCustomExtension')
    assert filter_extension_methods("MyCustomExtension", line, known_extensions)


def test_extension_method_requires_parentheses():
    line = 'users.Where'  # Without parentheses - not a call
    assert not filter_extension_methods("Where", line, set())


def test_extension_method_with_parentheses():
    line = 'users.Where(x => x.Id > 0)'
    assert filter_extension_methods("Where", line, set())


def test_extension_method_with_generic():
    line = 'users.Select<User, int>(x => x.Id)'
    assert filter_extension_methods("Select", line, set())
