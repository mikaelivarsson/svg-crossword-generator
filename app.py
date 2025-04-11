from flask import Flask, render_template, request, send_file
from markupsafe import Markup
import subprocess
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    svg_markup = None
    svg_file = None
    crossword_data = ""
    highlight_data = ""
    clue_data = ""
    decor_data = ""

    if request.method == 'POST':
        crossword_data = request.form['crossword_data']
        highlight_data = request.form['highlight_data']
        clue_data = request.form['clue_data']
        decor_data = request.form['decor_data']

        combined_data = request.form['combined_data'] 
        
        if not crossword_data: # if the textarea is empty
            crossword_data = "\n"
        # Create a temporary input file

        input_file = "temp_crossword.txt"
        with open(input_file, 'w') as f:
            f.write(combined_data)

        # Run the crossword script
        output_file_facit = "temp_crossword_facit.svg"
        subprocess.run(['python', 'korsord.py', input_file], check=True)

        # Read the generated SVG file
        try:
            with open(output_file_facit, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            svg_markup = Markup(svg_content)
        except FileNotFoundError:
            svg_markup = "SVG generation failed."

        # Clean up temporary files
        os.remove(input_file)

        crossword_data = '\n' + crossword_data

        return render_template('index.html', svg_markup=svg_markup, svg_file=output_file_facit, crossword_data=crossword_data, highlight_data=highlight_data, clue_data=clue_data, decor_data=decor_data)

    else: #if method is GET
        crossword_data = "\n   S\n   V\n   G\n   \n   C\n   R\n   O\n   S\n   S\n   W\n   O\n   R\n   D\n   \n   G\n   E\n   N\n   E\n   R\n   A\n   T\n   O\n   R\n"
        clue_data = "A1H1 15 (HP)\nA2H1 15 AD\nA3H1 15 AR\nA4H1 15 AU\nA5H1 15 BR\nA6H1 15 BRD\nA7H1 15 BUR\nA8H1 15 C\nA9H1 15 CD\nA10H1 15 CL\nA11H1 15 CR\nA12H1 15 DH\nA13H1 15 DH2\nA14H1 15 DH3\nA15H1 15 DH4\nA16H1 15 DR\nA17H1 15 DV\nA18H1 15 LH\nA19H1 15 RD\nA20H1 15 RR\nA21H1 15 TD\nA22H1 15 TR\nA23H1 15 UR\n" 
        highlight_data = "B1"
        decor_data = "B2 AD\nB3 AR\nB4 AU\nB5 BR\nB6 BRD\nB7 BUR\nB8 C\nB9 CD\nB10 CL\nB11 CR\nB12 DH\nB13 DH2\nB14 DH3\nB15 DH4\nB16 DR\nB17 DV\nB18 LH\nB19 RD\nB20 RR\nB21 TD\nB22 TR\nB23 UR\n"

    return render_template('index.html', crossword_data=crossword_data, highlight_data=highlight_data, clue_data=clue_data, decor_data=decor_data)

@app.route('/download_svg')
def download_svg():
    svg_file = request.args.get('file')
    if svg_file and os.path.exists(svg_file):
        return send_file(svg_file, as_attachment=True, download_name='crossword.svg')
    else:
        return "SVG file not found.", 404

if __name__ == '__main__':
    app.run(debug=True, port=5010)
