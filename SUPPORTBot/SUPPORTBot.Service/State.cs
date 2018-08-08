using System;
using System.Collections.Concurrent;
using System.Threading.Tasks;
using SUPPORTBot.Service.Abstraction;

namespace SUPPORTBot.Service
{
    public enum MyState
    {
        Start,
        CreatingTicket, 
        EditingTicket,
        AppendingTicket
    }
    
    public class State : IState<MyState>
    {
        private readonly ConcurrentDictionary<string, MyState> _stateDictionary = new ConcurrentDictionary<string, MyState>();

        public async Task CreateState(string user, MyState state)
        {
            _stateDictionary.AddOrUpdate(user, state, (k, v) => state);
        }

        public async Task<MyState> GetState(string user)
        {
            return _stateDictionary[user];
        }
    }
}