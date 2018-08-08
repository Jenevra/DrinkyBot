using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using SUPPORTBot.Service;
using SUPPORTBot.Service.Abstraction;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;

namespace SUPPORTBot.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ValuesController : ControllerBase
    {
        
        private readonly IUpdateService _updateService;
        public ValuesController(IUpdateService updateService, IState<MyState> state)
        {
            _updateService = updateService;
        }
        

        // GET api/values/5
        [HttpGet("{id}")]
        public ActionResult<string> Get(int id)
        {
            return "value";
        }

        // POST api/values
        [HttpPost]
        [HttpPost]
        public async Task<IActionResult> Post([FromBody] Update update)
        {
            await _updateService.UpdateHandler(update);
            return Ok();
        }
        


        
    }
}