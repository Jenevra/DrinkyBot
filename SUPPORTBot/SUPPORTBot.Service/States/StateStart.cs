using System.Security.Cryptography.X509Certificates;
using Telegram.Bot.Types.ReplyMarkups;

namespace SUPPORTBot.Service
{
    public class StateStart
    {
        public static InlineKeyboardMarkup GenerateCreateTicketKeyboard()
        {
            return new InlineKeyboardMarkup(InlineKeyboardButton.WithCallbackData("Создать заявку", "Заявка"));
        }

        public static InlineKeyboardMarkup GenerateCancelTicketKeyboard()
        {
            return new InlineKeyboardMarkup(InlineKeyboardButton.WithCallbackData("Отменить заявку", "Отмена"));
        }
    }
}