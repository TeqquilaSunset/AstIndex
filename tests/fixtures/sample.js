
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
