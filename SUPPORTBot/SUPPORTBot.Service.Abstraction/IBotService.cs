using System;
using Telegram.Bot;

namespace SUPPORTBot.Service.Abstraction
{
    public interface IBotService
    {
        TelegramBotClient Client { get;  }
    }
}