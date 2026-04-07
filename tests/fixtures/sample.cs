
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
