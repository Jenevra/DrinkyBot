using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using SUPPORTBot.Service.Abstraction;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;

namespace SUPPORTBot.Service
{
    
    
    public class UpdateService : IUpdateService
    {
        private readonly IBotService _botService;
        private readonly ILogger<UpdateService> _logger;
        private readonly IState<MyState> _state;

        private string GetUserId(Update update)
        {
            var type = update.Type;
            return type == UpdateType.CallbackQuery ? update.CallbackQuery.From.Id.ToString() : update.Message.From.Id.ToString();
        }
        
//        private List<MyButton> _buttons = new List<MyButton>()
//        {
//            new MyButton("Заявка", query => Task.CompletedTask),
//            new MyButton("Дополнение", query => Task.CompletedTask),
//            new MyButton("Отправление", query => Task.CompletedTask),
//            new MyButton("Отмена", query => Task.CompletedTask),
//            new MyButton("Отмена редакт", query => Task.CompletedTask),
//            new MyButton("Дополнение", query => Task.CompletedTask)
//        };

        public UpdateService(IBotService botService, ILogger<UpdateService> logger, IState<MyState> state)
        {
            _botService = botService;
            _logger = logger;
            _state = state;
        }

        
        public async Task UpdateHandler(Update update)
        
        {
            var userId = GetUserId(update);
            if (update.Message != null && update.Message.Text == "/start")
            {
                
                var message = update.Message;
                
                _logger.LogDebug("Creating user {0}", message.From.Id);
                
                var inlineKeyboard = StateStart.GenerateCreateTicketKeyboard();
                await _botService.Client.SendTextMessageAsync(userId,
                    "Привет. Я оператор службы поддержки. Если у Вас есть вопросы, оставьте заявку.",
                    replyMarkup: inlineKeyboard);
                await _state.CreateState(userId, MyState.Start);
            }

            
            var state = await _state.GetState(userId);
            
            switch (state)
            {
                case MyState.Start:
                {
                    if (update.CallbackQuery != null)
                    {
                        var inlineKeyboard = StateStart.GenerateCancelTicketKeyboard();
                        
                        await _botService.Client.SendTextMessageAsync(userId,
                            "Пожалуйста, опишите Вашу проблему.",
                            replyMarkup: inlineKeyboard);
                        await _state.CreateState(userId, MyState.CreatingTicket);  
                    }
                    break;
                }
                case MyState.CreatingTicket:
                {
                    if (update.CallbackQuery != null)
                    {
                        await _botService.Client.SendTextMessageAsync(userId,
                            "Благодарим за обращение. Будем рады помочь вновь.");
                    }

                    if (update.Message != null)
                    {
                        var inlineKeyboard = StateCreating.GenerateContinueEditKeyboard();
        
                        await _botService.Client.SendTextMessageAsync(userId,
                            "Вы хотите продолжить ввод?",
                            replyMarkup: inlineKeyboard);
                        await _state.CreateState(userId, MyState.EditingTicket);
                    }
                    break;
                }
                case MyState.EditingTicket:
                {
                    if (update.CallbackQuery != null)
                    {
                        var textMessage = StateEditing.Swtich(update.CallbackQuery);
                        await _botService.Client.SendTextMessageAsync(userId, textMessage.Result); 
                    }
                    break;
                }  
            } 
        }


//        class MyButton
//        {
//            private readonly string _callbackData;
//            private readonly Func<CallbackQuery, Task> _handler;
//            private string CallbackData { get; }
//
//            public Task Handle(CallbackQuery query)
//            {
//                return _handler(query);
//            }
//            
//            public MyButton(string callbackData, Func<CallbackQuery, Task> handler)
//            {
//                CallbackData = callbackData;
//                _handler = handler;
//            }
//        }


        
    }
}