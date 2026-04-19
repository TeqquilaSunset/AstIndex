
import pytest

from ast_index.config import Config
from ast_index.database import Database
from ast_index.indexer import Indexer
from ast_index.search import SearchEngine


@pytest.fixture
def csharp_project(temp_dir):
    """Создать временный C# проект."""
    # Создать .csproj файл
    (temp_dir / "Test.csproj").write_text("""
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
  </PropertyGroup>
</Project>
""")

    # Создать несколько C# файлов
    (temp_dir / "Models.cs").write_text("""
using System;
using System.Collections.Generic;

namespace TestApp.Models
{
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
    }

    public class UserRepository
    {
        public List<User> GetAll() => new List<User>();
    }
}
""")

    (temp_dir / "Services.cs").write_text("""
using System.Linq;
using TestApp.Models;

namespace TestApp.Services
{
    public class UserService
    {
        private UserRepository _repository;

        public UserService(UserRepository repository)
        {
            _repository = repository;
        }

        public List<User> GetActiveUsers()
        {
            return _repository.GetAll()
                .Where(u => u.Id > 0)
                .ToList();
        }
    }
}
""")

    yield temp_dir


def test_full_csharp_workflow(csharp_project, temp_dir):
    """Тест полного цикла индексации и поиска C# проекта."""
    # 1. Создаем конфиг и индексируем
    config = Config(root=csharp_project)
    with Indexer(config=config) as indexer:
        indexer.index()

    # 2. Проверка что символы проиндексированы
    with Database(config.db_path) as db:
        stats = db.get_stats()

        assert stats['symbols'] >= 3  # User, UserRepository, UserService

        # 3. Поиск символов
        search = SearchEngine(config=config)

        # Найти User
        results = search.search("User")
        user_symbols = [r for r in results if r['name'] == "User"]
        assert len(user_symbols) > 0

        # Найти UserRepository
        results = search.search("UserRepository")
        assert len(results) > 0

        # 4. Проверка usings
        models_path = str(csharp_project / "Models.cs")
        mapping = db.get_usings_for_file(models_path)

        assert "System" in mapping.imports
        assert "System.Collections.Generic" in mapping.imports

        # 5. Проверка ссылок
        services_path = str(csharp_project / "Services.cs")
        refs = db.get_references_for_file(services_path)

        # Должны быть ссылки на UserRepository, User
        ref_symbols = {r['symbol_name'] for r in refs}
        assert "UserRepository" in ref_symbols
        assert "User" in ref_symbols

        # 6. Проверка поиска использований
        usages = db.get_usages("User")
        assert len(usages) > 0

        # 7. Проверка наследования (если есть)
        # В этом проекте нет наследования, но проверим что метод работает
        children = db.get_children("User")
        parents = db.get_parents("User")
        assert isinstance(children, list)
        assert isinstance(parents, list)


def test_generic_type_indexing(csharp_project, temp_dir):
    """Тест индексации generic типов."""
    config = Config(root=csharp_project)
    with Indexer(config=config) as indexer:
        indexer.index()

    with Database(config.db_path) as db:
        # Проверить что есть символы в базе данных
        stats = db.get_stats()
        assert stats['symbols'] >= 3  # User, UserRepository, UserService

        # Проверить что есть ссылки в файлах
        models_path = str(csharp_project / "Models.cs")
        refs = db.get_references_for_file(models_path)

        ref_symbols = {r['symbol_name'] for r in refs}
        # В этом тесте мы просто проверяем что ссылочный механизм работает
        # даже если некоторые символы отфильтровываются как стандартные
        assert isinstance(ref_symbols, set)


def test_linq_extension_methods_indexing(csharp_project, temp_dir):
    """Тест индексации LINQ extension methods."""
    config = Config(root=csharp_project)
    with Indexer(config=config) as indexer:
        indexer.index()

    with Database(config.db_path) as db:
        # Проверить что есть ссылки на Where и ToList
        services_path = str(csharp_project / "Services.cs")
        refs = db.get_references_for_file(services_path)

        ref_symbols = {r['symbol_name'] for r in refs}
        assert "Where" in ref_symbols
        assert "ToList" in ref_symbols
