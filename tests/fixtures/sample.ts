
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
