import pytest
import tempfile
from pathlib import Path
import shutil

from ast_index.config import Config
from ast_index.database import Database
from ast_index.indexer import Indexer
from ast_index.search import SearchEngine


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file."""
    file_path = temp_dir / "sample.py"
    file_path.write_text('''
class BaseClass:
    """Base class."""
    def base_method(self):
        pass

class DerivedClass(BaseClass):
    """Derived class."""
    def __init__(self, value: int):
        self.value = value
    
    def get_value(self) -> int:
        return self.value

def standalone_function(name: str) -> str:
    """A standalone function."""
    return f"Hello, {name}"
''')
    return file_path


@pytest.fixture
def sample_csharp_file(temp_dir):
    """Create a sample C# file."""
    file_path = temp_dir / "Sample.cs"
    file_path.write_text("""
using System;

namespace Sample
{
    public interface ISample
    {
        void DoSomething();
    }
    
    public class BaseClass
    {
        public virtual void BaseMethod() { }
    }
    
    public class DerivedClass : BaseClass, ISample
    {
        public int Value { get; set; }
        
        public void DoSomething()
        {
            Console.WriteLine("Done");
        }
    }
}
""")
    return file_path


@pytest.fixture
def sample_javascript_file(temp_dir):
    """Create a sample JavaScript file."""
    file_path = temp_dir / "sample.js"
    file_path.write_text("""
class BaseClass {
    baseMethod() {
        return "base";
    }
}

class DerivedClass extends BaseClass {
    constructor(value) {
        super();
        this.value = value;
    }
    
    getValue() {
        return this.value;
    }
}

function standaloneFunction(name) {
    return `Hello, ${name}`;
}

const arrowFunction = (x, y) => x + y;
""")
    return file_path


@pytest.fixture
def sample_typescript_file(temp_dir):
    """Create a sample TypeScript file."""
    file_path = temp_dir / "sample.ts"
    file_path.write_text("""
interface ISample {
    doSomething(): void;
}

class BaseClass {
    baseMethod(): string {
        return "base";
    }
}

class DerivedClass extends BaseClass implements ISample {
    value: number;
    
    constructor(value: number) {
        super();
        this.value = value;
    }
    
    doSomething(): void {
        console.log("done");
    }
}

function standaloneFunction(name: string): string {
    return `Hello, ${name}`;
}

type Point = {
    x: number;
    y: number;
};

enum Status {
    Active,
    Inactive
}
""")
    return file_path


@pytest.fixture
def sample_project(temp_dir, sample_python_file, sample_javascript_file):
    """Create a sample project with multiple files."""
    return temp_dir


@pytest.fixture
def config(temp_dir):
    """Create a test config."""
    return Config(root=temp_dir)


@pytest.fixture
def database(temp_dir):
    """Create a test database."""
    db_path = temp_dir / "test.db"
    db = Database(str(db_path))
    yield db
    db.close()


@pytest.fixture
def indexer(config):
    """Create a test indexer."""
    idx = Indexer(config=config)
    yield idx
    idx.close()


@pytest.fixture
def search_engine(config):
    """Create a test search engine."""
    engine = SearchEngine(config=config)
    yield engine
    engine.close()
