# main.py

import logging
from uuid import uuid4
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, InputTextMessageContent
from telegram.ext import ApplicationBuilder, InlineQueryHandler, CommandHandler, ContextTypes
import matplotlib.pyplot as plt
import io
import asyncio
import os
import subprocess
from dotenv import load_dotenv, dotenv_values

def create_folders():
    # Directories for uploads and outputs
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def generate_latex_image(latex_code):
    # Generate LaTeX image using matplotlib
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.text(0.5, 0.5, latex_code, fontsize=16, ha='center', va='center')
    ax.axis('off')

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='jpeg', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    image_stream.seek(0)
    return image_stream



async def handle_tex_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.document.mime_type != 'application/x-tex':
        update.message.reply_text('Please send a .tex file.')
        return

    file = update.message.document
    file_id = file.file_id
    new_file = context.bot.get_file(file_id)
    file_path = os.path.join(UPLOAD_FOLDER, file.file_name)

    new_file.download(file_path)

    output_pdf = os.path.join(OUTPUT_FOLDER, os.path.splitext(file.file_name)[0] + '.pdf')
    command = f"pdflatex -output-directory={OUTPUT_FOLDER} {file_path}"

    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        update.message.reply_text('Failed to compile the TeX file:\n' + process.stderr.decode('utf-8'))
        return

    context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_pdf, 'rb'))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    logging.info(f'got query {query}')
    if query.startswith("$") and query.endswith("$"):
        latex_code = query

        # Define the maximum allowed length for the LaTeX code
        max_code_length = 200

        if  len(latex_code) > 1 and len(latex_code) <= max_code_length:
            image_stream = await generate_latex_image(latex_code)

            # Upload the image to Telegram and get the file_id
            photo = InputFile(image_stream, filename='latex.png')
            message = await context.bot.send_photo(chat_id=update.inline_query.from_user.id, photo=photo)
            file_id = message.photo[-1].file_id

            # Creating an InlineQueryResultPhoto
            results = [
                InlineQueryResultPhoto(
                    id=str(update.inline_query.id),
                    photo_url=f"https://api.telegram.org/file/bot{context.bot.token}/{file_id}",
                    thumbnail_url=f"https://api.telegram.org/file/bot{context.bot.token}/{file_id}",
                    title="LaTeX Image",
                    caption=query.strip('$')
                )
            ]
            await context.bot.answer_inline_query(update.inline_query.id, results=results)
        else:
            # Inform about wrong LaTeX code
            await context.bot.answer_inline_query(update.inline_query.id, results=[], switch_pm_text="Invalid LaTeX code length", switch_pm_parameter="start")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot. Use inline queries to generate LaTeX images.")

# Define options command handler like options_handler = CommandHandler('options', options)
async def options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Upload LaTeX File", callback_data='upload')],
        [InlineKeyboardButton("Generate LaTeX Image", callback_data='generate')],
        [InlineKeyboardButton("Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)

# Define button callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")


def main():
    create_folders()
    load_dotenv()
    TOKEN = os.getenv("API-KEY")
    if TOKEN:
        application = ApplicationBuilder().token(TOKEN).build()

        inline_handler = InlineQueryHandler(inline_query)
        start_handler = CommandHandler('start', start)
        options_handler = CommandHandler('options', options)

        application.add_handler(inline_handler)
        application.add_handler(start_handler)
        application.add_handler(options_handler)

        application.run_polling()
    else:
        print("NO API KEY GIVEN.")


if __name__ == "__main__":
    main()
