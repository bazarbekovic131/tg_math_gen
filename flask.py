from flask import Flask, send_from_directory
import psycopg2
from main import generate_latex_image

app = Flask(__name__)

@app.route('/images/<image_id>')
def serve_image(image_id):
    conn = psycopg2.connect(
        dbname="formulas",
        user="bazarbekovic",
        password="mobilisinmobile1839",
        host="localhost"
    )
    cur = conn.cursor()
    cur.execute("SELECT image_path FROM formulae WHERE id = %s", (image_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        image_path = result[0]
        return send_from_directory(directory='outputs', path=image_path.split('/')[-1])
    else:
        return "Image not found", 404

def get_latex_image(latex_code, filename, conn):
    try:
        cur = conn.cursor()
    except AttributeError as ae:
        print(f"error: {ae}")
        return 400

    cur.execute("SELECT id, latex_code FROM formulae")
    formulas = cur.fetchall()

    for formula_id, latex_code in formulas:
        filename = f"{formula_id}.png"
        image_path = generate_latex_image(latex_code, filename)
        cur.execute(
            "UPDATE formulae SET image_path = %s WHERE id = %s",
            (image_path, formula_id)
        )

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
