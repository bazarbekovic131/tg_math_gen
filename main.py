import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import matplotlib.pyplot as plt
import io
import os
import subprocess
import time
from dotenv import load_dotenv
from pdf2image import convert_from_path
import re
from PIL import Image


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
    ax.text(0.5, 0.5, f"${latex_code}$", fontsize=16, ha='center', va='center')
    ax.axis('off')

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='jpeg', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    image_stream.seek(0)
    return image_stream

async def process_latex_image(latex_code):
    tex_code = f"""
    \\documentclass[border = 1cm]{{standalone}}
    \\usepackage{{amsmath}}
    \\begin{{document}}
    {latex_code}
    \\end{{document}}
    """
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'

    tex_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, "temp.tex"))
    pdf_path = os.path.abspath(os.path.join(OUTPUT_FOLDER, "temp.pdf"))
    png_path = os.path.abspath(os.path.join(OUTPUT_FOLDER, "temp.png"))

    logging.info(f'{tex_path}')

    # Write the LaTeX code to a .tex file
    with open(tex_path, 'w') as f:
        f.write(tex_code)
        f.close()

    time.sleep(1)
    # Compile the LaTeX code to PDF using pdflatex
    # Compile the LaTeX code to PDF using pdflatex
    try:
        result = subprocess.run(
            ['pdflatex', '-output-directory', 'outputs', 'uploads/temp.tex'],
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logging.info(f"pdflatex output: {result.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.error(f"pdflatex error: {e.stderr.decode()}")
        raise e

    # Convert the PDF file to PNG using pdf2image
    pages = convert_from_path(pdf_path, dpi=300)
    pages[0].save(png_path, 'PNG')

    # Resize the image to acceptable dimensions
    max_size = (1280, 1280)
    with Image.open(png_path) as img:
        img.thumbnail(max_size)
        img.save(png_path)

    return png_path

async def handle_latex2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latex_code = (update.message.text.strip()).strip('$')
    
    if len(latex_code) > 1 and len(latex_code) <= 200:
        image_stream = await generate_latex_image(latex_code)

        # Send the generated image to the user
        photo = InputFile(image_stream, filename='latex.jpg')
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo, caption="Here is your LaTeX image.")
    else:
        await update.message.reply_text("Please provide a valid LaTeX code between 1 and 200 characters.")

def wrap_latex_code(latex_code):
    # Define patterns for LaTeX commands that need to be wrapped in math environment
    patterns = [
        r'\\begin{pmatrix}.*?\\end{pmatrix}',  # Environments like pmatrix
        r'\\[a-zA-Z]+(?:{[^}]+})*',  # General LaTeX commands with possible arguments
        r'\\frac{[^}]+}{[^}]+}',     # Fraction
        r'\\sqrt{[^}]+}',            # Square root
    ]

    # Combine all patterns into a single regex
    combined_pattern = '|'.join(patterns)
    combined_regex = re.compile(combined_pattern)

    def replacer(match):
        matched_text = match.group(0)
        # Check if the matched text is already wrapped
        if not (matched_text.startswith('$') and matched_text.endswith('$')):
            return f'$ {matched_text} $'
        return matched_text

    # Replace all matches in the LaTeX code
    wrapped_code = combined_regex.sub(replacer, latex_code)
    return wrapped_code

async def handle_latex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ### original
    latex_code = update.message.text.strip()
    context.user_data["awaiting_latex_code"] = True

    if context.user_data.get("awaiting_latex_code"):
        context.user_data["awaiting_latex_code"] = False

        if len(latex_code) > 1 and len(latex_code) <= 200:
            latex_code = wrap_latex_code(latex_code)  # Wrap the LaTeX code
            image_path = await process_latex_image(latex_code)

            # Send the generated image to the user
            with open(image_path, 'rb') as image_file:
                photo = InputFile(image_file, filename='latex.png')
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo, caption="Here is your LaTeX image.")
        else:
            await update.message.reply_text("Please provide a valid LaTeX code between 1 and 200 characters.")
    else:
        await handle_latex2(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a LaTeX code, and I'll generate an image for you.")

async def options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Generate LaTeX Image", callback_data='generate')],
        [InlineKeyboardButton("Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = (
            "To use this bot:\n"
            "- Send LaTeX code directly as a message to get an image of the rendered LaTeX.\n"
            "- Use the 'Generate LaTeX Image' option to start generating LaTeX images.\n"
            "- This bot supports simple LaTeX code between $ symbols (but it can be omitted).\n"
        )
        await query.edit_message_text(text=help_text)
    elif query.data == 'generate':
        context.user_data["awaiting_latex_code"] = True
        await query.edit_message_text(text="Please send the LaTeX code as a message to generate an image.")


def main():
    create_folders()
    load_dotenv()
    TOKEN = os.getenv("API-KEY")
    if TOKEN:
        application = ApplicationBuilder().token(TOKEN).build()

        start_handler = CommandHandler('start', start)
        options_handler = CommandHandler('options', options)
        message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_latex)
        button_handler = CallbackQueryHandler(button)

        application.add_handler(start_handler) # start info
        application.add_handler(options_handler) # Options are help
        application.add_handler(message_handler) # LaTeX code with or without $$
        application.add_handler(button_handler) # Callback

        application.run_polling()
    else:
        print("NO API KEY GIVEN.")

if __name__ == "__main__":
    main()
