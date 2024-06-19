import logging
from telegram import InlineQueryResultPhoto, Update, InputFile
from telegram.ext import ApplicationBuilder, InlineQueryHandler, CommandHandler, ContextTypes
import matplotlib.pyplot as plt
import io
import asyncio
import os
from dotenv import load_dotenv, dotenv_values



# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def generate_latex_image(latex_code):
    # Generate LaTeX image using matplotlib
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.text(0.5, 0.5, latex_code, fontsize=16, ha='center', va='center')
    ax.axis('off')
    
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    
    image_stream.seek(0)
    return image_stream

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
            # Introduce a timeout of 2 seconds before sending the image
            await context.bot.answer_inline_query(update.inline_query.id, results=[], switch_pm_text="Invalid LaTeX code length", switch_pm_parameter="start")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot. Use inline queries to generate LaTeX images.")


def main():
    load_dotenv()
    TOKEN = os.getenv("API-KEY")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    inline_handler = InlineQueryHandler(inline_query)
    start_handler = CommandHandler('start', start)
    
    application.add_handler(inline_handler)
    application.add_handler(start_handler)
    
    application.run_polling()


if __name__ == "__main__":
    main()
