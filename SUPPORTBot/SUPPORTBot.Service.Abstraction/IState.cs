using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SUPPORTBot.Service.Abstraction
{
    public interface IState<T>
    {
        Task CreateState(string user, T state);
        Task<T> GetState(string user);
        
    }
}