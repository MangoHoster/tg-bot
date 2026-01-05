import os
import sys
import io
import traceback
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 12345))

bot = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def send_output(message, output, filename="output.txt"):
    if len(output) > 4096:
        with io.BytesIO(str.encode(output)) as out_file:
            out_file.name = filename
            await message.reply_document(
                document=out_file,
                caption="Output is too long, sent as file."
            )
    else:
        await message.reply_text(f"<pre>{output}</pre>")

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    button = [[InlineKeyboardButton("Source Code", url="https://github.com/MangoHoster/tg-bot")]]
    await message.reply_text(
        "Hello I'm alive",
        reply_markup=InlineKeyboardMarkup(button)
    )

@bot.on_message(filters.command('sh') & filters.user(OWNER_ID))
async def shell_command(client, message):
    if len(message.text.split()) < 2:
        return await message.reply("No command provided.")
    
    cmd = message.text.split(maxsplit=1)[1]
    msg = await message.reply("**Processing...**", quote=True)
    
    try:
        shell_output = subprocess.getoutput(cmd)
        await msg.delete()
        await send_output(message, shell_output, "shell.txt")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

@bot.on_message(filters.command("eval") & filters.user(OWNER_ID))
async def eval_command(client: Client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply_text("Please provide code to evaluate!")
        return

    cmd = message.text.split(" ", 1)[1]
    msg = await message.reply("**Processing...**", quote=True)

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc()
    
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    await msg.delete()
    await send_output(message, evaluation, "eval.txt")

async def aexec(code, client, message):
    exec(
        f'async def __ex(client, message): ' +
        ''.join(f'\n {line}' for line in code.split('\n'))
    )
    return await locals()['__ex'](client, message)

if __name__ == "__main__":
    print("Bot is starting...")
    bot.run()
