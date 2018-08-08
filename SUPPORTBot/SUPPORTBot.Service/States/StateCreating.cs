using Telegram.Bot.Types.ReplyMarkups;

namespace SUPPORTBot.Service
{
    public class StateCreating
    {
        public static InlineKeyboardMarkup GenerateContinueEditKeyboard()
        {
            return new InlineKeyboardMarkup(new []
            {
                InlineKeyboardButton.WithCallbackData("Дополнить", "Дополнение"),
                InlineKeyboardButton.WithCallbackData("Отправить", "Отправление"),
                InlineKeyboardButton.WithCallbackData("Отменить заявку", "Отмена редакт")
            });
        }
    }
}