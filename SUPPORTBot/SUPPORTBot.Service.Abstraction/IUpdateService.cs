using System.Threading.Tasks;
using Telegram.Bot.Types;

namespace SUPPORTBot.Service.Abstraction
{
    public interface IUpdateService
    {
        Task UpdateHandler(Update update);
    }
}