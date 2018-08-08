using System;
using System.Net;
using System.Net.Http;
using Microsoft.Extensions.Options;
using SUPPORTBot.Service.Abstraction;
using Telegram.Bot;

namespace SUPPORTBot.Service
{
    public class BotService : IBotService
    {
        private readonly BotConfiguration _config;

        public BotService(IOptions<BotConfiguration> config)
        {
            _config = config.Value;
            Client = new TelegramBotClient(_config.BotToken, GetClient());
        }
        
        private static HttpClient GetClient()
        {
            var handler = new HttpClientHandler
            {
                Proxy = new WebProxy
                {
                    Address = new Uri("http://217.61.104.163:3128"),
                    UseDefaultCredentials = false,
                    Credentials = new NetworkCredential
                    {
                        UserName = "user1",
                        Password = "neverlostpassword"
                    }
                }
            };
            return new HttpClient(handler);
        }

        public TelegramBotClient Client { get; }
    }
}