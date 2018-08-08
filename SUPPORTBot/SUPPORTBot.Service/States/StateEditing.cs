using System.Threading.Tasks;
using Telegram.Bot.Types;

namespace SUPPORTBot.Service
{
    public class StateEditing
    {
        public static async Task<string> Swtich(CallbackQuery update)
        {
            var message = "";
            switch (update.Data)
            {
                case "Дополнение":
                    message = "Введите свое сообщение.";
                    break;
                case "Отправление":
                    message = "Ваша заявка находится в обработке.";
                    break;
                case "Отмена редакт":
                    message = "Благодарим за обращение. Будем рады помочь вновь.";
                    break;      
            }

            return message;
        }
    }
}