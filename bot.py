import os
import sys
import io
import traceback
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 12345))

async def send_output(update: Update, context: ContextTypes.DEFAULT_TYPE, output: str, filename: str = "output.txt"):
    if len(output) > 4096:
        with io.BytesIO(str.encode(output)) as out_file:
            out_file.name = filename
            await update.message.reply_document(
                document=out_file,
                caption="Output is too long, sent as file."
            )
    else:
        await update.message.reply_text(f"<pre>{output}</pre>", parse_mode='HTML')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = [[InlineKeyboardButton("Source Code", url="https://github.com/MangoHoster/tg-bot")]]
    reply_markup = InlineKeyboardMarkup(button)
    
    await update.message.reply_text(
        "Hello I'm alive",
        reply_markup=reply_markup
    )

async def shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("No command provided.")
        return
    
    cmd = ' '.join(context.args)
    msg = await update.message.reply_text("**Processing...**")
    
    try:
        shell_output = subprocess.getoutput(cmd)
        await msg.delete()
        await send_output(update, context, shell_output, "shell.txt")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def eval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Please provide code to evaluate!")
        return

    cmd = ' '.join(context.args)
    msg = await update.message.reply_text("**Processing...**")

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec(cmd, context, update)
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
    await send_output(update, context, evaluation, "eval.txt")

async def aexec(code: str, context: ContextTypes.DEFAULT_TYPE, update: Update):
    exec(
        f'async def __ex(context, update): ' +
        ''.join(f'\n {line}' for line in code.split('\n'))
    )
    return await locals()['__ex'](context, update)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sh", shell_command))
    application.add_handler(CommandHandler("eval", eval_command))
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
